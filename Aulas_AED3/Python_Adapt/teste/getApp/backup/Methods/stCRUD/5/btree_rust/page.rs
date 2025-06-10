//! Implementations of different disk page types.
//!
//! # Page Types
//!
//! Currently there are 3 types of disk pages:
//!
//! - [`Page`]: Used for BTree nodes. This is the most common type of page,
//! that's why it's called literally "Page". It is also the most complex type
//! of page because it's a slotted page that stores [`Cell`] instances instead
//! of just raw bytes.
//!
//! - [`PageZero`]: Special subtype of [`Page`] which holds additional metadata
//! about the database file. As such, it contains less usable space than a
//! normal BTree [`Page`], which introduces some edge cases that have to be
//! addressed at [`super::btree`].
//!
//! - [`OverflowPage`]: Used when variable size data exceeds the maximum amount
//! of bytes allowed in a single page. [`OverflowPage`] instances are also
//! reused as free pages because they both share the same headers, that's the
//! purpose of the [`FreePage`] type alias.
//!
//! # Other Data Structures
//!
//! The cache buffer needs to be able to store all kinds of pages, but we know
//! the exact type of page that we need at compile time, so there's no need for
//! dynamic dispatch and traits. Instead, we group all the pages into the
//! [`MemPage`] enum and store that in the cache. Then we use [`TryFrom`] to
//! extract the type we need.
//!
//! There's another important data structure in this module that serves as the
//! basic building block for any kind of page, which is [`BufferWithHeader`].
//! Since all pages have a header followed by some content, we might as well try
//! to reuse some of the code. Right now we're doing so with the [Newtype]
//! pattern which introduces some boilerplate but it's not too bad.
//!
//! [Newtype]: https://rust-unofficial.github.io/patterns/patterns/behavioural/newtype.html
//!
//! # The Database File
//!
//! Each database is stored in a single file, and the data structures in this
//! module operate on pages of such file. The DB file looks roughly like this:
//!
//! ```text
//! +--------------------------+ <----+
//! |       File Metadata      |      |
//! +--------------------------+      |
//! | +----------------------+ |      |
//! | | Btree Page 0 Header  | |      | PAGE 0    struct PageZero
//! | +----------------------+ |      |
//! | | Btree page 0 Content | |      |
//! | +----------------------+ |      |
//! +--------------------------+ <----+
//! | +----------------------+ |      |
//! | | Btree Page 1 Header  | |      |
//! | |                      | |      |
//! | +----------------------+ |      | PAGE 1    struct Page
//! | | Btree page 1 Content | |      |
//! | |                      | |      |
//! | +----------------------+ |      |
//! +--------------------------+ <----+
//! | +----------------------+ |      |
//! | | Btree Page 2 Header  | |      |
//! | |                      | |      |
//! | +----------------------+ |      | PAGE 2    struct Page
//! | | Btree page 2 Content | |      |
//! | |                      | |      |
//! | +----------------------+ |      |
//! +--------------------------+ <----+
//! | +----------------------+ |      |
//! | | Overflow Page Header | |      |
//! | |                      | |      |
//! | +----------------------+ |      | PAGE 3    struct OverflowPage
//! | |   Overflow Content   | |      |
//! | |                      | |      |
//! | +----------------------+ |      |
//! +--------------------------+ <----+
//! | +----------------------+ |      |
//! | |    Fee Page Header   | |      |
//! | |                      | |      |
//! | +----------------------+ |      | PAGE 4    struct OverflowPage (AKA FreePage)
//! | |        UNUSED        | |      |
//! | |                      | |      |
//! | +----------------------+ |      |
//! +--------------------------+ <----+
//!             ...
//! ```
//!
//! Pages link to other pages using their [`PageNumber`], which is just a 32 bit
//! offset that can be used to jump from the beginning of the file to a
//! concrete page. As an exception, pointing to page 0 is the same as saying
//! "NULL" or "None", since nobody can point to page 0. BTree pages do not point
//! to their parents, and even if page 0 itself is used as a BTree page it only
//! points downwards to its children, so nobody ever should point to page 0.
//!
//! All the data structures in this module offer higher level APIs to operate on
//! a single page. For operations involving multiples pages at the same time see
//! the [`super::btree`] module.
//!
//! # Module Structure Notes
//!
//! TODO: This module could be split into something like this:
//!
//! ```text
//! |-- page/
//!     |-- buffer.rs
//!     |-- mem.rs
//!     |-- mod.rs
//!     |-- overflow.rs
//!     |-- slotted.rs
//!     |-- zero.rs
//! ```
//!
//! But for now we're trying to maintain two levels of nesting in this project
//! to prevent it from becoming complicated to navigate. At the moment there's
//! only one directory per subsystem so it's pretty clear where everything is.

use std::{
    alloc::{self, Allocator, Layout},
    any,
    collections::{BinaryHeap, HashMap},
    fmt::{self, Debug},
    iter,
    mem::{self, ManuallyDrop},
    ops::{Bound, RangeBounds},
    ptr::{self, NonNull},
};

use crate::paging::pager::PageNumber;

/// Magic number at the beginning of the database file.
///
/// `0xB74EE` is supposed to stand for "BTree" and also serves as endianess
/// check, since the big endian and little endian representations are different.
pub(crate) const MAGIC: u32 = 0xB74EE;

/// Maximum page size is 64 KiB.
pub(crate) const MAX_PAGE_SIZE: usize = 64 << 10;

/// Minimum acceptable page size.
///
/// When in debug mode the minimum value of the page size is calculated so that
/// a normal [`Page`] instance can store at least one valid [`Cell`], which is
/// an aligned cell that can fit [`CELL_ALIGNMENT`] bytes.
///
/// In numbers, at the moment of writing this the page header is 12 bytes, a
/// slot pointer is 2 bytes, and the cell header is 8 bytes. This gives us a
/// total of 22 bytes of metadata for one single payload.
///
/// [`CELL_ALIGNMENT`] is 8 bytes, so we'll consider that to be the minimum
/// payload. Essentially what we do is add 8 bytes to 22 bytes, giving us 30
/// bytes, and then we align upwards to 32 bytes. So the minimum page size in
/// debug mode can store only 8 bytes worth of data, but we allow this because
/// most tests use really small page sizes for simplicity and because it's
/// easier to debug.
///
/// In release mode we'll consider the minimum size to be 512 bytes.
pub(crate) const MIN_PAGE_SIZE: usize = if cfg!(debug_assertions) {
    (PAGE_HEADER_SIZE + SLOT_SIZE + CELL_HEADER_SIZE + 2 * CELL_ALIGNMENT as u16 - 1) as usize
        & !(CELL_ALIGNMENT - 1)
} else {
    512
};

/// Size of the [`Page`] header. See [`PageHeader`] for details.
pub(crate) const PAGE_HEADER_SIZE: u16 = mem::size_of::<PageHeader>() as _;

/// Size of the database file header.
pub(crate) const DB_HEADER_SIZE: u16 = mem::size_of::<DbHeader>() as _;

/// Size of [`CellHeader`].
pub(crate) const CELL_HEADER_SIZE: u16 = mem::size_of::<CellHeader>() as _;

/// Size of an individual slot (offset pointer).
pub(crate) const SLOT_SIZE: u16 = mem::size_of::<u16>() as _;

/// See the "Alignment" section of the [`Page`] documentation for alignment
/// details.
///
/// Briefly, cells in each [`Page`] must be aligned to 8 bytes for simplicity.
pub(crate) const CELL_ALIGNMENT: usize = mem::align_of::<CellHeader>();

/// Page memory buffer alignment.
///
/// We're using the `O_DIRECT` flag on Linux to bypass the OS cache. `O_DIRECT`
/// requires that buffers are aligned to at least the logical block size of the
/// block device, which is usually 512 bytes. We're going to align all the pages
/// to the file system block size, which is typically 4096 bytes.
///
/// TODO: This should be a parameter that we supply at runtime when we
/// initialize the database and check the file system block size, but right now
/// that requires a lot of changes throughout the codebase so we'll just use
/// this patch instead.
///
/// Basically [`BufferWithHeader::alloc`] should take a [`Layout`] as a
/// parameter instead of only the page size, but all the builders for structs
/// in the codebase where written assuming that the page alignment is the same
/// as the [`CELL_ALIGNMENT`] before discovering the `O_DIRECT` alignment bug.
/// The kernel raises Os Error 22 if memory buffers are not aligned to block
/// sizes when using `O_DIRECT`, check the man page for open(). Anyway, this
/// needs refactoring, TODO.
pub(crate) const PAGE_ALIGNMENT: usize = 4096;

/// The slot array can be indexed using 2 bytes, since it will never be bigger
/// than [`MAX_PAGE_SIZE`].
pub(crate) type SlotId = u16;

/// In-memory binary buffer split into header and content.
///
/// This struct is the basic building block for all the pages and contains a
/// single memory buffer that looks like this:
///
/// ```text
/// +----- Buffer address
/// |
/// |        +----- Content offset  (Buffer address + size of header)
/// |        |
/// V        V
/// +--------+--------------------------+
/// | HEADER |         CONTENT          |
/// +--------+--------------------------+
/// ```
///
/// The struct provides methods for directly reading or writing both the header
/// and the content. The size in bytes of the header is determined by the
/// generic type `H` using [`mem::size_of`].
///
/// References to the entire memory buffer (including both the header and the
/// content) can be obtained using [`AsRef::as_ref`] and [`AsMut::as_mut`].
struct BufferWithHeader<H> {
    /// Pointer to the header located at the beginning of the buffer.
    header: NonNull<H>,
    /// Pointer to the content located right after the header.
    content: NonNull<[u8]>,
    /// Total size of the buffer (size of header + size of content).
    size: usize,
}

impl<H> BufferWithHeader<H> {
    /// Allocates a pointer that can fit a page buffer of the given `size`.
    ///
    /// `size` in this case refers to the complete size of the buffer, not the
    /// size of the content or size of the header, but the sum of both. The
    /// returned allocation has all its bytes set to 0.
    ///
    /// # Panics
    ///
    /// Panics if `size <= mem::size_of::<H>()`. In other words, the buffer must
    /// be able to fit an entire header plus at least one byte. Otherwise
    /// accessing the content is undefined behaviour.
    ///
    /// Additionally this function also panics if `size` does not meet the
    /// requirements of [`alloc::Layout::from_size_align`]. Basically, make sure
    /// that `size` rounded up to [`PAGE_ALIGNMENT`] does not overflow.
    /// [`isize::MAX`].
    ///
    /// TODO: See [`PAGE_ALIGNMENT`], this needs refactoring.
    pub fn alloc(size: usize) -> NonNull<[u8]> {
        assert!(
            size > mem::size_of::<H>(),
            "attempt to allocate {} of insufficient size: size of {} is {} while allocation size is {}",
            any::type_name::<Self>(),
            any::type_name::<H>(),
            mem::size_of::<H>(),
            size,
        );

        // TODO: We can probably handle the alloc error by rolling back the
        // database and returning an error to the client.
        alloc::Global
            .allocate_zeroed(alloc::Layout::from_size_align(size, PAGE_ALIGNMENT).unwrap())
            .expect("could not allocate BufferWithHeader<H>")
    }

    /// Returns a new buffer of the given size where all the bytes are 0.
    ///
    /// If the fields of the header need values other than 0 for initialization
    /// then they should be written manually after this function call.
    pub fn new(size: usize) -> Self {
        // SAFETY: [`Self::alloc`] meets all the requirements of
        // [`Self::from_non_null`] since it checks the pointer size and it uses
        // [`PAGE_ALIGNMENT`].
        unsafe { Self::from_non_null(Self::alloc(size)) }
    }

    /// Same as [`Self::new`] but checks that the page size is within bounds.
    ///
    /// # Panics
    ///
    /// Panics if the page size is less than [`MIN_PAGE_SIZE`] or greater than
    /// [`MAX_PAGE_SIZE`].
    pub fn for_page(size: usize) -> Self {
        assert!(
            (MIN_PAGE_SIZE..=MAX_PAGE_SIZE).contains(&size),
            "page size {size} is not a value between {MIN_PAGE_SIZE} and {MAX_PAGE_SIZE}"
        );

        Self::new(size)
    }

    /// Constructs a new buffer from the given [`NonNull`] pointer.
    ///
    /// # Safety
    ///
    /// This function is marked as unsafe even though it checks some
    /// preconditions because the caller must ensure that the destructors run
    /// in the correct order. The requirements depend on the use case.
    ///
    /// ## Case 1: Fully Owned, Allocated Buffer
    ///
    /// 1. If this [`BufferWithHeader`] is intended to "own" the given `pointer`
    /// and deallocate it after it goes out of scope then `pointer` must have
    /// been allocated using [`BufferWithHeader::alloc`] to ensure the memory
    /// layout is correct. Mainly, the pointer should be aligned to
    /// [`PAGE_ALIGNMENT`].
    ///
    /// ## Case 2: Buffer Contained Within Larger Buffer
    ///
    /// 1. If this [`BufferWithHeader`] is intended to exist within another
    /// larger buffer or allocation then its destructor must never run as it
    /// would try to free the given `pointer`. Use [`mem::ManuallyDrop`] or
    /// [`mem::forget`] to prevent this bug.
    ///
    /// 2. After the larger buffer or allocation is dropped, this inner buffer
    /// cannot be used anymore since that would be a use after free.
    ///
    /// 3. Alignment in this must still be at least [`CELL_ALIGNMENT`] to
    /// satisfy the alignment requirements of BTree pages. [`PageZero`] stores
    /// an instance of [`Page`] inside its buffer so that's why we check the
    /// [`CELL_ALIGNMENT`].
    ///
    /// # Panics
    ///
    /// Panics if the pointer has insufficient length or is not aligned to
    /// [`CELL_ALIGNMENT`].
    pub unsafe fn from_non_null(pointer: NonNull<[u8]>) -> Self {
        assert!(
            pointer.len() > mem::size_of::<H>(),
            "attempt to construct {} from invalid pointer of size {} when size of {} is {}",
            any::type_name::<Self>(),
            pointer.len(),
            any::type_name::<H>(),
            mem::size_of::<H>(),
        );

        assert!(
            pointer.is_aligned_to(CELL_ALIGNMENT),
            "attempt to create {} from unaligned pointer {:?}",
            any::type_name::<Self>(),
            pointer
        );

        let content = NonNull::slice_from_raw_parts(
            pointer.byte_add(mem::size_of::<H>()).cast::<u8>(),
            Self::usable_space(pointer.len()) as usize,
        );

        Self {
            header: pointer.cast(),
            content,
            size: pointer.len(),
        }
    }

    /// Similar to [`NonNull::cast`].
    ///
    /// Transforms this buffer into a buffer with a different header type.
    pub fn cast<T>(self) -> BufferWithHeader<T> {
        let Self {
            header,
            content,
            size,
        } = self;

        assert!(
            size > mem::size_of::<T>(),
            "cannot cast {} of total size {size} to {} where the size of {} is {}",
            any::type_name::<Self>(),
            any::type_name::<BufferWithHeader<T>>(),
            any::type_name::<T>(),
            mem::size_of::<T>(),
        );

        mem::forget(self);

        let header = header.cast();

        let content = unsafe {
            NonNull::slice_from_raw_parts(
                header.byte_add(mem::size_of::<T>()).cast::<u8>(),
                BufferWithHeader::<T>::usable_space(size) as usize,
            )
        };

        BufferWithHeader {
            header,
            content,
            size,
        }
    }

    /// Number of bytes that can be used to store content.
    ///
    /// ```text
    ///                 usable_space()
    ///          +--------------------------+
    ///          |                          |
    ///          V                          V
    /// +--------+--------------------------+
    /// | HEADER |         CONTENT          |
    /// +--------+--------------------------+
    /// ```
    pub fn usable_space(size: usize) -> u16 {
        (size - mem::size_of::<H>()) as u16
    }

    /// Returns a read-only reference to the header.
    pub fn header(&self) -> &H {
        // SAFETY: If we allocated the buffer then we know the pointer is valid.
        // Otherwise the caller must have ensured so when calling
        // [`Self::from_non_null`].
        unsafe { self.header.as_ref() }
    }

    /// Returns a mutable reference to the header.
    pub fn header_mut(&mut self) -> &mut H {
        // SAFETY: Same as [`Self::header`].
        unsafe { self.header.as_mut() }
    }

    /// Returns a read-only reference to the content part of this buffer.
    pub fn content(&self) -> &[u8] {
        // SAFETY: Pretty much the same as [`Self::header`], if the pointer
        // passes all the checks that we need then accessing the content should
        // be ok.
        unsafe { self.content.as_ref() }
    }

    /// Returns a mutable reference to the content part of this buffer.
    pub fn content_mut(&mut self) -> &mut [u8] {
        // SAFETY: Same as [`Self::content`].
        unsafe { self.content.as_mut() }
    }

    /// Returns a [`NonNull`] pointer to the entire in-memory buffer.
    fn as_non_null(&self) -> NonNull<[u8]> {
        NonNull::slice_from_raw_parts(self.header.cast::<u8>(), self.size)
    }

    /// Returns a byte slice of the entire buffer including its header.
    fn as_slice(&self) -> &[u8] {
        // SAFETY: What we've already discussed in [`Self::header`] and
        // [`Self::content`].
        unsafe { self.as_non_null().as_ref() }
    }

    /// Returns a mutable byte slice of the entire buffer including its header.
    fn as_slice_mut(&mut self) -> &mut [u8] {
        // SAFETY: At this point you should already get the idea :)
        unsafe { self.as_non_null().as_mut() }
    }

    /// Consumes `self` and returns a pointer to the underlying memory buffer.
    ///
    /// The buffer must be dropped by the caller after this function returns.
    pub fn into_non_null(self) -> NonNull<[u8]> {
        ManuallyDrop::new(self).as_non_null()
    }
}

impl<H> AsRef<[u8]> for BufferWithHeader<H> {
    fn as_ref(&self) -> &[u8] {
        self.as_slice()
    }
}

impl<H> AsMut<[u8]> for BufferWithHeader<H> {
    fn as_mut(&mut self) -> &mut [u8] {
        self.as_slice_mut()
    }
}

impl<H> PartialEq for BufferWithHeader<H> {
    fn eq(&self, other: &Self) -> bool {
        self.as_ref().eq(other.as_ref())
    }
}

impl<H> Clone for BufferWithHeader<H> {
    fn clone(&self) -> Self {
        let mut cloned = Self::new(self.size);
        cloned.as_slice_mut().copy_from_slice(self.as_slice());

        cloned
    }
}

impl<H: Debug> Debug for BufferWithHeader<H> {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        f.debug_struct("BufferWithHeader")
            .field("size", &self.size)
            .field("header", self.header())
            .field("content", &self.content())
            .finish()
    }
}

impl<H> Drop for BufferWithHeader<H> {
    fn drop(&mut self) {
        // SAFETY: Read [`Self::from_non_null`] and [`Self::alloc`].
        unsafe {
            alloc::Global.deallocate(
                self.header.cast(),
                alloc::Layout::from_size_align(self.size, PAGE_ALIGNMENT).unwrap(),
            )
        }
    }
}

/// Cell header located at the beginning of each cell.
///
/// The header stores the size of the cell without including its own size and it
/// also stores a pointer to the BTree page the contains entries "less than"
/// this one.
///
/// ```text
///           HEADER                               CONTENT
/// +-----------------------+-----------------------------------------------+
/// | +------+------------+ |                                               |
/// | | size | left_child | |                                               |
/// | +------+------------+ |                                               |
/// +-----------------------+-----------------------------------------------+
///                         ^                                               ^
///                         |                                               |
///                         +-----------------------------------------------+
///                                            size bytes
/// ```
///
/// # Alignment
///
/// Cells are 64 bit aligned. See [`Page`] for more details.
///
/// # Overflow
///
/// The maximum size of a cell is defined by [`Page::ideal_max_payload_size`].
/// If a cell needs to hold more data than its maximum size allows, then we'll
/// set [`CellHeader::is_overflow`] to `true` and make the last 4 bytes of the
/// content point to an [`OverflowPage`].
#[derive(Debug, PartialEq, Clone, Copy)]
#[repr(C, align(8))]
pub(crate) struct CellHeader {
    /// Size of the cell content.
    size: u16,

    /// True if this cell points to an overflow page.
    ///
    /// Since we need to add
    /// padding to align the fields of this struct anyway, we're not wasting
    /// space here.
    pub is_overflow: bool,

    /// Add padding manually to avoid uninitialized bytes.
    ///
    /// The [`PartialEq`] implementation for [`Page`] relies on comparing the
    /// memory buffers, but Rust does not make any guarantees about the values
    /// of padding bytes. See here:
    ///
    /// <https://github.com/rust-lang/unsafe-code-guidelines/issues/174>
    padding: u8,

    /// Page number of the BTree page that contains values less than this cell.
    pub left_child: PageNumber,
}

/// A cell is a structure that stores a single BTree entry.
///
/// Each cell stores the binary entry (AKA payload or key) and a pointer to the
/// BTree node that contains cells with keys smaller than that stored in the
/// cell itself.
///
/// The [`super::BTree`] structure reorders cells around different sibling pages
/// when an overflow or underflow occurs, so instead of hiding the low level
/// details we provide some API that can be used by upper levels.
///
/// # About DSTs
///
/// Note that this struct is a DST (Dynamically Sized Type), which is hard to
/// construct in Rust and is considered a "half-baked feature" (as of march 2024
/// at least, check the [nomicon]). Not that half-baked features are a problem,
/// we're using nightly and `#![feature()]` everywhere to see the latest and
/// greatest of Rust, but it would be nice to have a standard way of building
/// DSTs.
///
/// [nomicon]: https://web.archive.org/web/20240222131917/https://doc.rust-lang.org/nomicon/exotic-sizes.html
///
/// The reason we're using this instead of anything else is because we need to
/// take both references and mutable references to cells and we also need owned
/// cells. Without DSTs we would need to define 3 types and implement the exact
/// same methods for all of them. Here's the last [commit] with multiple types
/// before the refactor.
///
/// [commit]: https://github.com/antoniosarosi/mkdb/blob/73e806fab193d79a41c9946bb7a0cbfba372e619/src/storage/page.rs#L608-L714
///
/// The other approach would be reusing [`BufferWithHeader`] again but at this
/// point I kinda got tired of the newtype boilerplate and using
/// `*buf.header_mut().field = other.header().field` instead of simply
/// `buf.header.field = other.header.field` so I tried something different
/// here.
///
/// The code at [`super::btree`] accesses [`Cell::header`] and [`Cell::content`]
/// many times and assigns specific values of one cell header to another cell
/// header and doing that through function calls is just too verbose. The DST
/// approach reduces boilerplate but makes it harder to construct the type at
/// runtime. See [`Page::cell_at_offset`] and [`Cell::new`] for details.
#[derive(Debug, PartialEq)]
pub(crate) struct Cell {
    /// Cell header.
    pub header: CellHeader,

    /// Cell content.
    ///
    /// If [`CellHeader::is_overflow`] is true then the last 4 bytes of this
    /// array should point to an overflow page.
    pub content: [u8],
}

impl Cell {
    /// Creates a new cell allocated in memory.
    pub fn new(mut payload: Vec<u8>) -> Box<Self> {
        let size = Self::aligned_size_of(&payload);
        // Add padding.
        payload.resize(size as _, 0);

        // SAFETY: Read below, basically CELL_ALIGNMENT makes this "safe".
        let mut buf = unsafe {
            let layout =
                Layout::from_size_align((size + CELL_HEADER_SIZE) as usize, CELL_ALIGNMENT)
                    .unwrap();

            let ptr = alloc::Global
                .allocate_zeroed(layout)
                .expect("Cell allocatio error");

            BufferWithHeader::<CellHeader>::from_non_null(ptr)
        };

        // Everything is set to 0 because we used allocate_zeroed, we only need
        // to change this.
        buf.header_mut().size = size;

        // TODO: The public API requires a [`Vec`] as payload but that's not
        // optimal since we have to copy the vec into a new buffer that contains
        // the header at the beginning. We should implement some custom type
        // "PayloadBuffer" or something similar that behaves exactly like
        // [`Vec`] buf already stores the header at the beginning and we can
        // simply take its pointer.
        buf.content_mut().copy_from_slice(&payload);

        // This is the DST hard part. In theory, all we need to build the DST
        // is a fat pointer, which is basically a two-tuple in the form of
        // (address, size). Note that "size" in this context is not the same
        // thing as the pointer length. The "size" here refers to the number
        // of elements that the DST stores in its dynamic part. If we allocate
        // 100 bytes but the DST stores 80 bytes because the first 20 correspond
        // to the header, then the size of the DST is 80, not 100.
        //
        // It's a bit counterintuitive because you'd think the size of the DST
        // should be the total length of the pointer, but it's not the case. The
        // size is only used for correctly indexing the dynamic part within its
        // bounds. Everything else is known at compile time.
        //
        // The other tricky part is that we have to create a "fake" slice and
        // then cast it to our DST. And then the other tricky part is that we
        // must meet the [`Box`] memory layout requirements because we're
        // boxing our DST pointer, so we better align those bytes if we want
        // the deallocation to be "safe" when [`Drop`] is called on the [`Box`]
        // instance. See here:
        //
        // <https://doc.rust-lang.org/std/boxed/index.html#memory-layout>
        //
        // [`Box`] uses [`Layout::for_value`] to obtain the memory layout, but
        // we can't do that because we don't have the value yet, we need to
        // build it first.
        //
        // The alignment is not a problem because we use [`CELL_ALIGNMENT`] when
        // allocating the pointer and then the size of the allocation shouldn't
        // be a problem either because we're adding padding manually. So when
        // [`Box`] calls [`Layout::for_value`] to drop the allocation it
        // obtains the exact same layout that we used above to allocate the
        // pointer originally.
        //
        // We could implement our own smart pointer that knows the exact layout
        // needed to deallocate and use that instead of [`Box`], but we're lazy
        // and this works for now. See other similar examples in the Rust
        // playground:
        //
        // Example 1: <https://play.rust-lang.org/?version=stable&mode=debug&edition=2021&gist=ce193d6fdcd9477463071cfa53d329b8>
        // Example 2: <https://play.rust-lang.org/?version=stable&mode=debug&edition=2018&gist=fd082276db55c278b3a37b4380ca912a>
        //
        // The second one comes from this Reddit discussion:
        // <https://www.reddit.com/r/rust/comments/mq3kqe/is_this_the_best_way_to_do_custom_dsts_unsized/>
        //
        // And the first one is a simplified version of the second one that I
        // wrote.
        //
        // Another important note that you should remember when reading this
        // codebase is that I don't know what I'm doing, so don't trust me on
        // this one, if it seg faults it seg faults :)
        unsafe {
            Box::from_raw(ptr::slice_from_raw_parts(
                buf.into_non_null().cast::<u8>().as_ptr(),
                payload.len(),
            ) as *mut Cell)
        }
    }

    /// Creates a new overflow cell by extending the `payload` buffer with the
    /// `overflow_page` number.
    pub fn new_overflow(mut payload: Vec<u8>, overflow_page: PageNumber) -> Box<Self> {
        payload.extend_from_slice(&overflow_page.to_le_bytes());

        let mut cell = Self::new(payload);
        cell.header.is_overflow = true;

        cell
    }

    /// Returns the first overflow page of this cell.
    pub fn overflow_page(&self) -> PageNumber {
        if !self.header.is_overflow {
            return 0;
        }

        PageNumber::from_le_bytes(
            self.content[self.content.len() - mem::size_of::<PageNumber>()..]
                .try_into()
                .expect("failed parsing overflow page number"),
        )
    }

    /// Total size of the cell including the header.
    pub fn total_size(&self) -> u16 {
        CELL_HEADER_SIZE + self.header.size
    }

    /// Total size of the cell including the header and the slot array pointer
    /// needed to store the offset.
    pub fn storage_size(&self) -> u16 {
        self.total_size() + SLOT_SIZE
    }

    /// See [`Page`] for details.
    pub fn aligned_size_of(data: &[u8]) -> u16 {
        Layout::from_size_align(data.len(), CELL_ALIGNMENT)
            .unwrap()
            .pad_to_align()
            .size() as u16
    }
}

impl Clone for Box<Cell> {
    fn clone(&self) -> Self {
        self.as_ref().to_owned()
    }
}

impl ToOwned for Cell {
    type Owned = Box<Self>;

    fn to_owned(&self) -> Self::Owned {
        let cell = ptr::from_ref(self);

        let owned = alloc::Global
            .allocate(Layout::for_value(self))
            .expect("alloc error while cloning cell")
            .as_non_null_ptr();

        // SAFETY: See [`Cell::new`].
        unsafe {
            owned.copy_from_nonoverlapping(
                NonNull::new_unchecked(cell.cast_mut().cast()),
                self.total_size() as usize,
            );

            Box::from_raw(owned.as_ptr().with_metadata_of(cell))
        }
    }
}

/// Slotted page header.
///
/// It is located at the beginning of each page and it does not contain variable
/// length data:
///
/// ```text
///                           HEADER                                          CONTENT
/// +-------------------------------------------------------------+----------------------------+
/// | +------------+-----------+------------------+-------------+ |                            |
/// | | free_space | num_slots | last_used_offset | right_child | |                            |
/// | +------------+-----------+------------------+-------------+ |                            |
/// +-------------------------------------------------------------+----------------------------+
///                                          PAGE
/// ```
///
/// The alignment and size of this struct doesn't matter. Actual data is
/// appended towards to end of the page, and the page should be aligned to 8
/// bytes. See [`Page`] for more details.
#[derive(Debug)]
#[repr(C)]
pub(crate) struct PageHeader {
    /// Amount of free bytes in this page.
    free_space: u16,

    /// Length of the slot array.
    num_slots: u16,

    /// Offset of the last inserted cell counting from the start of the content.
    ///
    /// ```text
    ///     count start        last_used_offset
    ///          |                    |
    ///          V                    V
    /// +--------+-------+------------+------+-----+------+
    /// | HEADER | SLOTS | FREE SPACE | CELL | DEL | CELL |
    /// +--------+-------+------------+------+-----+------+
    ///          ^                                        ^
    ///          |                                        |
    ///          +-----------------------------------------
    ///                         Page Content
    /// ```
    ///
    /// For empty pages with no cells, this value is equal to the content size:
    ///
    /// ```text
    ///                                             last_used_offset
    ///                                                   |
    ///                                                   V
    /// +--------+----------------------------------------+
    /// | HEADER |              EMPTY PAGE                |
    /// +--------+----------------------------------------+
    ///          ^                                        ^
    ///          |                                        |
    ///          +-----------------------------------------
    ///                        Page Content
    /// ```
    ///
    /// This makes it so that there is no distinction between empty pages and
    /// pages with cells, we can always substract the size of a cell from
    /// `last_used_offset` to obtain the next `last_used_offset`.
    ///
    /// The reason we start counting from the beginning of the content instead
    /// of the header is because [`MAX_PAGE_SIZE`] equals 65536 (2^16) while
    /// [`u16::MAX`] is equal to 65535 (2^16 - 1) so the trick mentioned above
    /// to reduce the algorithm to one single case would not work with 64 KiB
    /// pages.
    ///
    /// We could store this as [`u32`] and remove the padding below but that
    /// introduces its own problems since doing arithmetic with [`u16`], [`u32`]
    /// and [`usize`] requires a bunch of casts everywhere. Here's the last
    /// commit where `last_used_offset` was [`u32`]:
    ///
    /// <https://github.com/antoniosarosi/mkdb/blob/7f4819dec0b1bc310d72e95e4af6858beb7b00f6/src/storage/page.rs#L502-L541>
    last_used_offset: u16,

    /// Add padding manually to avoid uninitialized bytes.
    ///
    /// The [`PartialEq`] implementation for [`Page`] relies on comparing the
    /// memory buffers, but Rust does not make any guarantees about the values
    /// of padding bytes. See here:
    ///
    /// <https://github.com/rust-lang/unsafe-code-guidelines/issues/174>
    padding: u16,

    /// Last child of this page.
    pub right_child: PageNumber,
}

impl PageHeader {
    /// Initializes a new header for empty pages.
    fn new(size: usize) -> Self {
        Self {
            num_slots: 0,
            last_used_offset: (size - PAGE_HEADER_SIZE as usize) as u16,
            free_space: Page::usable_space(size),
            right_child: 0,
            padding: 0,
        }
    }
}

/// Fixed size slotted page.
///
/// This is the most important data structure here since it allows us to store
/// BTree nodes on disk, which are used for both indexes and tables. The page
/// maintains a "slot array" located after the header that grows towards the
/// right. On the opposite side is where used cells are located, leaving free
/// space in the middle of the page. Each item in the slot array points to one
/// of the used cells through its offset, calculated from the start of the slot
/// array (after the [`PageHeader`]).
///
/// ```text
///   HEADER   SLOT ARRAY       FREE SPACE             USED CELLS
///  +------+----+----+----+------------------+--------+--------+--------+
///  |      | O1 | O2 | O3 | ->            <- | CELL 3 | CELL 2 | CELL 1 |
///  +------+----+----+----+------------------+--------+--------+--------+
///           |    |    |                     ^        ^        ^
///           |    |    |                     |        |        |
///           +----|----|---------------------|--------|--------+
///                |    |                     |        |
///                +----|---------------------|--------+
///                     |                     |
///                     +---------------------+
/// ```
///
/// This is useful for 2 reasons, described below.
///
/// # Cheap Sorting or Reordering
///
/// First, we can rearrange cells without changing their physical location. We
/// only need to change the offsets in the slot array. For example, if we wanted
/// to reverse the order of the cells in the figure above, this is all we need
/// to do:
///
/// ```text
///   HEADER   SLOT ARRAY       FREE SPACE             USED CELLS
///  +------+----+----+----+------------------+--------+--------+--------+
///  |      | O3 | O2 | O1 | ->            <- | CELL 3 | CELL 2 | CELL 1 |
///  +------+----+----+----+------------------+--------+--------+--------+
///           |    |    |                     ^        ^        ^
///           |    |    |                     |        |        |
///           +----|----|---------------------+        |        |
///                |    |                              |        |
///                +----|-------------------------------        |
///                     |                                       |
///                     +---------------------------------------+
/// ```
///
/// Now the third cell becomes the first one in the list, second cell stays
/// the same and the first cell becomes the last. Changing offsets in the slot
/// array is much cheaper than moving the cells around the page. This is needed
/// for BTree pages to sort entries, and this is the only feature implemented
/// here.
///
/// # Maintaining Slot Positions After Delete Operations
///
/// The second reason this is useful is because we could maintain the same slot
/// number for the rest of the cells when one of them is deleted. For example,
/// if we deleted CELL 2 in the figure above, we wouldn't necessarily have to
/// compact the slot array like this:
///
/// ```text
///   HEADER SLOT ARRAY       FREE SPACE              USED CELLS
///  +------+----+----+----------------------+--------+--------+--------+
///  |      | O3 | O1 | ->                <- | CELL 3 |   DEL  | CELL 1 |
///  +------+----+----+----------------------+--------+--------+--------+
///           |    |                         ^                 ^
///           |    |                         |                 |
///           +----|-------------------------+                 |
///                |                                           |
///                +-------------------------------------------+
/// ```
///
/// If we did this, then the slot ID of CELL 1 would change from 2 to 1. But
/// instead we could simply set the slot to NULL or zero:
///
/// ```text
///   HEADER SLOT ARRAY       FREE SPACE              USED CELLS
///  +------+----+----+----+------------------+--------+--------+--------+
///  |      | O3 |NULL| O1 | ->            <- | CELL 3 |   DEL  | CELL 1 |
///  +------+----+----+----+------------------+--------+--------+--------+
///           |         |                     ^                 ^
///           |         |                     |                 |
///           +---------|---------------------+                 |
///                     |                                       |
///                     +---------------------------------------+
/// ```
///
/// The remaining slot IDs do not change. This is useful for deleting tuples
/// and delaying index updates as much as possible if using tuple oriented
/// storage, which we are not doing, so you'll never see NULL slots.
///
/// # Null Slots
///
/// Initially this was going to be a generic slotted page implementation that
/// would serve as a building block for both index organized storage (like
/// SQLite) and tuple oriented storage (like Postgres), but the idea has been
/// dropped in favor of simplicity.
///
/// The main difference is that when using index organized storage we never
/// point to slot indexes from outside the page, so there's no need to attempt
/// to maintain their current position for as long as possible. This [commit]
/// contains the last version that used to do so. Another benefit of the current
/// aproach (index organized storage) is that BTree nodes and disk pages are the
/// same thing, because everything is stored in a BTree, so we need less
/// generics, less types and less code. Take a look at the [btree.c] file from
/// SQLite 2.X.X for the inspiration.
///
/// Check these lectures for some background on slotted pages and data storage:
///
/// - [F2023 #03 - Database Storage Part 1 (CMU Intro to Database Systems)](https://www.youtube.com/watch?v=DJ5u5HrbcMk)
/// - [F2023 #04 - Database Storage Part 2 (CMU Intro to Database Systems)](https://www.youtube.com/watch?v=Ra50bFHkeM8)
///
/// [commit]: https://github.com/antoniosarosi/mkdb/blob/3011003170f02d337f62cdd9f5af0f3b63786144/src/paging/page.rs
/// [btree.c]: https://github.com/antoniosarosi/sqlite2-btree-visualizer/blob/master/src/btree.c
///
/// # Alignment
///
/// In-memory pages need to be aligned to hardware block size or file system
/// block sizes (which are multiples of the hardware block sizes). That's needed
/// for DMA stuff when bypassing kernel buffering with flags like `O_DIRECT` on
/// Linux.
///
/// On the other hand, [`CellHeader`] instances must be 64 bit aligned, which in
/// turn will make the first content byte of each cell 64 bit aligned. And
/// that's needed to make sure tuples (rows) are stored at aligned memory
/// addresses so that we can interpret a column as a value without decoding any
/// bytes. For example, if we have some schema like `[BigInt, Varchar(255), Bool]`
/// we should make sure that the first `BigInt` number is aligned to 8 bytes.
/// The [`Page`] API only ensures that the starting address of the row is
/// aligned to 8 bytes, but alignment within the tuple itself must be controlled
/// at upper layers. Inner tuple alignmnet is NOT YET implemented, see
/// [`super::tuple`] for details.
///
/// # Overflow
///
/// Slotted pages are fixed size, so if we keep inserting cells into them at
/// some point they will "overflow". A [`Page`] is considered "overflow" if it
/// contains at least one cell that did not fit in the fixed size available
/// space. Do not confuse this with [`OverflowPage`], which are used to store
/// large binary contents on disk in a linked list of pages.
///
/// To deal with [`Page`] overflow we maintain a hash map of cells that didn't
/// fit in the slotted page where we store the index where they should have been
/// inserted in the slotted array.
///
/// ```text
///   HEADER   SLOT ARRAY  FREE SPACE        USED CELLS
///  +------+----+----+----+--------+--------+--------+--------+
///  |      | O1 | O2 | O3 | ->  <- | CELL 3 | CELL 2 | CELL 1 |
///  +------+----+----+----+--------+--------+--------+--------+
///           |    |    |           ^        ^        ^
///           |    |    |           |        |        |
///           +----|----|-----------|--------|--------+
///                |    |           |        |
///                +----|-----------|--------+
///                     |           |
///                     +-----------+
///
///  +---------+
///  | OVF MAP |
///  +---------+
///  |   |     |        +------------+
///  | 1 | PTR | -----> | BOXED CELL |
///  |   |     |        +------------+
///  +---------+
///  |   |     |        +------------+
///  | 3 | PTR | -----> | BOXED CELL |
///  |   |     |        +------------+
///  +---+-----+
/// ```
///
/// In the figure above, the contents of the overflow map indicate that slot
/// indexes 1 and 3 correspond to the boxed cells that we are storing outside of
/// the page.
///
/// Not all methods take overflow into account however, most of them don't care
/// because once the page overflows the BTree balancing algorithm will move all
/// the cells out of the page and reorganize them across siblings. The only
/// method that needs to work correctly is [`Page::drain`] as that's the one
/// used to move the cells out.
///
/// The idea of this approach is to avoid initializing an in-memory copy of the
/// slot array every time we load a page into the buffer pool like SQLite
/// does. See this [line].
///
/// [line]: https://github.com/antoniosarosi/sqlite2-btree-visualizer/blob/master/src/btree.c#L329
///
/// A similar implementation was tried in the past. See [here].
///
/// [here]: https://github.com/antoniosarosi/mkdb/blob/b20b37631351647cf89185e7710db10af0de2157/src/storage/page.rs#L806-L876
///
/// It was discarded mostly because it adds too much overhead for almost no
/// benefit at all since we are not going to constantly work with overflow
/// pages. Overflow pages are some sort of "exceptional" state.
///
/// So in the current implementation a page is loaded from disk "as is", without
/// any additional initialization. The overflow overhead only kicks in when a
/// page actually overflows.
///
/// # Notes
///
/// This struct contains a lot of boilerplate, better start by reading the most
/// important methods which are [`Self::try_insert`], [`Self::defragment`],
/// [`Self::try_replace`] and [`Self::remove`]. Those work on the fixed size
/// slotted page and don't care about overflow. Then there are wrappers that
/// account for the overflow state: [`Self::insert`] and [`Self::replace`].
/// And the most important low level unsafe API is [`Self::cell_at_offset`].
#[derive(Clone)]
pub(crate) struct Page {
    /// Fixed size in-memory buffer that contains the data read from disk.
    buffer: BufferWithHeader<PageHeader>,
    /// Overflow map.
    overflow: HashMap<SlotId, Box<Cell>>,
}

// TODO: Technically two pages could have the exact same content but different
// internal structure due to calls to defragment or different insertion order.
// However figuring out if the cells are actually equal probably requires an
// O(n^2) algorithm. This is good enough for tests anyway, as the BTree always
// inserts data in the same order.
impl PartialEq for Page {
    fn eq(&self, other: &Self) -> bool {
        self.buffer == other.buffer
    }
}

impl AsRef<[u8]> for Page {
    fn as_ref(&self) -> &[u8] {
        self.buffer.as_ref()
    }
}

impl AsMut<[u8]> for Page {
    fn as_mut(&mut self) -> &mut [u8] {
        self.buffer.as_mut()
    }
}

impl<H> From<BufferWithHeader<H>> for Page {
    fn from(buffer: BufferWithHeader<H>) -> Self {
        let mut buffer = buffer.cast();

        *buffer.header_mut() = PageHeader::new(buffer.size);

        Self {
            buffer,
            overflow: HashMap::new(),
        }
    }
}

impl Page {
    /// Allocates a new page of `size` bytes in memory.
    pub fn alloc(size: usize) -> Self {
        Self::from(BufferWithHeader::<PageHeader>::for_page(size))
    }

    /// Amount of space that can be used in a page to store [`Cell`] instances.
    ///
    /// Since [`MAX_PAGE_SIZE`] is 64 KiB, the usable space should be a value
    /// less than [`u16::MAX`] unless the header of the page is zero sized,
    /// which doesn't make much sense anyway.
    pub fn usable_space(page_size: usize) -> u16 {
        BufferWithHeader::<PageHeader>::usable_space(page_size)
    }

    /// The maximum payload size that can be stored in the given usable space.
    ///
    /// It's calculated by substracting the cell header size and the slot
    /// pointer size from the usable space and then aligning the result
    /// downwards to [`CELL_ALIGNMENT`]. This makes sure that at least one cell
    /// can successfuly fit in the given space.
    fn max_payload_size_in(usable_space: u16) -> u16 {
        (usable_space - CELL_HEADER_SIZE - SLOT_SIZE) & !(CELL_ALIGNMENT as u16 - 1)
    }

    /// Maximum size that the payload of a single [`Cell`] should take on the
    /// page to allow the page to store at least `min_cells`.
    pub fn ideal_max_payload_size(page_size: usize, min_cells: usize) -> u16 {
        debug_assert!(
            min_cells > 0,
            "if you're not gonna store any cells then why are you even calling this function?"
        );

        let ideal_size =
            Self::max_payload_size_in(Self::usable_space(page_size) / min_cells as u16);

        debug_assert!(
            ideal_size > 0,
            "page size {page_size} is too small to store {min_cells} cells"
        );

        ideal_size
    }

    /// Similar to [`Self::ideal_max_payload_size`] but allows a cell to occupy
    /// as much as possible.
    ///
    /// See [`Self::insert`] for more details.
    fn max_allowed_payload_size(&self) -> u16 {
        Self::max_payload_size_in(Self::usable_space(self.size()))
    }

    /// Size in bytes of the page.
    pub fn size(&self) -> usize {
        self.buffer.size
    }

    /// Number of cells in the page.
    ///
    /// If the page is in "overflow" state the returned number includes the
    /// overflow cells.
    pub fn len(&self) -> u16 {
        self.header().num_slots + self.overflow.len() as u16
    }

    /// Returns `true` if this page doesn't store any cells.
    pub fn is_empty(&self) -> bool {
        self.len() == 0
    }

    /// Reference to the page header.
    pub fn header(&self) -> &PageHeader {
        self.buffer.header()
    }

    /// Mutable reference to the page header.
    pub fn header_mut(&mut self) -> &mut PageHeader {
        self.buffer.header_mut()
    }

    /// Pointer to the slot array.
    fn slot_array_non_null(&self) -> NonNull<[u16]> {
        NonNull::slice_from_raw_parts(self.buffer.content.cast(), self.header().num_slots as usize)
    }

    // Slotted array as a slice.
    fn slot_array(&self) -> &[u16] {
        // SAFETY: See [`BufferWithHeader::content_non_null`].
        unsafe { self.slot_array_non_null().as_ref() }
    }

    // Slotted array as a mutable slice.
    fn slot_array_mut(&mut self) -> &mut [u16] {
        // SAFETY: See [`BufferWithHeader::content_non_null`].
        unsafe { self.slot_array_non_null().as_mut() }
    }

    /// Returns a pointer to the [`CellHeader`] located at the given `offset`.
    ///
    /// # Safety
    ///
    /// This function is marked as `unsafe` because we can't guarantee the
    /// offset is valid within the function, so the caller is responsible for
    /// that.
    unsafe fn cell_header_at_offset(&self, offset: u16) -> NonNull<CellHeader> {
        self.buffer.content.byte_add(offset as usize).cast()
    }

    /// Returns a pointer to the [`Cell`] located at the given offset.
    ///
    /// # Safety
    ///
    /// Same as [`Self::cell_header_at_offset`].
    unsafe fn cell_at_offset(&self, offset: u16) -> NonNull<Cell> {
        let header = self.cell_header_at_offset(offset);
        let size = header.as_ref().size as usize;

        // See the giant comment in [`Cell::new`] for the "DST construction"
        // explanation. Basically make a fake slice that tells the compiler
        // what the address of the DST is and how many elements the DST stores
        // in its dynamic part.
        let cell = ptr::slice_from_raw_parts(header.cast::<u8>().as_ptr(), size) as *mut Cell;

        NonNull::new_unchecked(cell)
    }

    /// Returns a pointer to the [`Cell`] located at the given slot.
    fn cell_at_slot(&self, index: SlotId) -> NonNull<Cell> {
        debug_assert!(
            index < self.header().num_slots,
            "slot index {index} out of bounds for slot array of length {}",
            self.header().num_slots
        );

        // SAFETY: The slot array always stores valid offsets within the page
        // that point to actual initialized cells.
        unsafe { self.cell_at_offset(self.slot_array()[index as usize]) }
    }

    /// Read-only reference to a cell.
    ///
    /// Returned lifetime is tied to that of the page itself.
    pub fn cell(&self, index: SlotId) -> &Cell {
        let cell = self.cell_at_slot(index);
        // SAFETY: Same as [`Self::cell_at_offset`].
        unsafe { cell.as_ref() }
    }

    /// Mutable reference to a cell.
    pub fn cell_mut(&mut self, index: SlotId) -> &mut Cell {
        let mut cell = self.cell_at_slot(index);
        // SAFETY: Same as [`Self::cell_at_offset`].
        unsafe { cell.as_mut() }
    }

    /// Returns an owned cell by cloning it.
    pub fn owned_cell(&self, index: SlotId) -> Box<Cell> {
        self.cell(index).to_owned()
    }

    /// Returns the child at the given `index`.
    ///
    /// Remember that the number of children is always `num_slots + 1`. There's
    /// always one more child than keys, that's why we return `right_child` if
    /// the index is exactly the length of the keys.
    pub fn child(&self, index: SlotId) -> PageNumber {
        if index == self.len() {
            self.header().right_child
        } else {
            self.cell(index).header.left_child
        }
    }

    /// Iterates over all the children pointers in this page.
    pub fn iter_children(&self) -> impl DoubleEndedIterator<Item = PageNumber> + '_ {
        let len = if self.is_leaf() { 0 } else { self.len() + 1 };

        (0..len).map(|i| self.child(i))
    }

    /// Returns `true` if this page is underflow.
    ///
    /// An ordinary page is in "underflow" condition when less than half of
    /// its usable space is occupied. Special cases must be handled at other
    /// layers.
    pub fn is_underflow(&self) -> bool {
        self.header().free_space > Self::usable_space(self.size()) / 2
    }

    /// Returns `true` if this page is overflow.
    pub fn is_overflow(&self) -> bool {
        !self.overflow.is_empty()
    }

    /// Number of used bytes in this page.
    pub fn used_bytes(&self) -> u16 {
        Self::usable_space(self.size()) - self.header().free_space
    }

    /// Number of free bytes in this page.
    pub fn free_space(&self) -> u16 {
        self.header().free_space
    }

    /// Returns `true` if this page has no children.
    pub fn is_leaf(&self) -> bool {
        self.header().right_child == 0
    }

    /// Adds `cell` to this page, possibly overflowing the page.
    pub fn push(&mut self, cell: Box<Cell>) {
        self.insert(self.len(), cell);
    }

    /// Inserts the `cell` at `index`, possibly overflowing.
    pub fn insert(&mut self, index: SlotId, cell: Box<Cell>) {
        assert!(
            cell.content.len() <= self.max_allowed_payload_size() as usize,
            "attempt to store payload of size {} when max allowed payload size is {}",
            cell.content.len(),
            self.max_allowed_payload_size()
        );

        assert!(
            index <= self.len(),
            "index {index} out of bounds for page of length {}",
            self.len()
        );

        if self.is_overflow() {
            self.overflow.insert(index, cell);
        } else if let Err(cell) = self.try_insert(index, cell) {
            self.overflow.insert(index, cell);
        }
    }

    /// Attempts to replace the cell at `index` with `new_cell`.
    ///
    /// It causes the page to overflow if it's not possible. After that, this
    /// function should not be called anymore.
    pub fn replace(&mut self, index: SlotId, new_cell: Box<Cell>) -> Box<Cell> {
        debug_assert!(
            !self.is_overflow(),
            "overflow cells are not replaced so replace() should not run on overflow pages"
        );

        match self.try_replace(index, new_cell) {
            Ok(old_cell) => old_cell,

            Err(new_cell) => {
                let old_cell = self.remove(index);
                self.overflow.insert(index, new_cell);
                old_cell
            }
        }
    }

    /// Attempts to insert the given `cell` in this page.
    ///
    /// There are two possible cases:
    ///
    /// - Case 1: the cell fits in the "free space" between the slot array and
    /// the closest cell. This is the best case scenario since we can just write
    /// the new cell without doing anything else.
    ///
    /// ```text
    ///   HEADER SLOT ARRAY       FREE SPACE              USED CELLS
    ///  +------+----+----+----------------------+--------+--------+--------+
    ///  |      | O3 | O1 | ->                <- | CELL 3 |   DEL  | CELL 1 |
    ///  +------+----+----+----------------------+--------+--------+--------+
    ///                               ^
    ///                               |
    ///           Both the new cell plus the slot fit here
    /// ```
    ///
    /// - Case 2: the cell fits in this page but we have to defragment first.
    /// This is the worst case scenario, but at least it does some garbage
    /// collection. See [`Self::defragment`] for details.
    ///
    /// ```text
    ///   HEADER SLOT ARRAY       FREE SPACE              USED CELLS
    ///  +------+----+----+----------------------+--------+--------+--------+
    ///  |      | O3 | O1 | ->                <- | CELL 3 |   DEL  | CELL 1 |
    ///  +------+----+----+----------------------+--------+--------+--------+
    ///                               ^                        ^
    ///                               |                        |
    ///                               +------------+-----------+
    ///                                            |
    ///                            We can fit the cell plus the slot
    ///                            if we join all the free space into
    ///                            one contiguous block
    /// ```
    ///
    /// There is no free list, we don't search for deleted blocks that can fit
    /// the new cell.
    fn try_insert(&mut self, index: SlotId, cell: Box<Cell>) -> Result<SlotId, Box<Cell>> {
        let cell_storage_size = cell.storage_size();

        // There's no way we can fit the cell in this page.
        if self.header().free_space < cell_storage_size {
            return Err(cell);
        }

        // Space between the end of the slot array and the closest cell.
        let available_space = {
            let end = self.header().last_used_offset;
            let start = self.header().num_slots * SLOT_SIZE;
            end - start
        };

        // We can fit the new cell but we have to defragment the page first.
        if available_space < cell_storage_size {
            self.defragment();
        }

        let offset = self.header().last_used_offset - cell.total_size();

        // Write new cell.
        // SAFETY: `last_used_offset` keeps track of where the last cell was
        // written. By substracting the total size of the new cell to
        // `last_used_offset` we get a valid pointer within the page where we
        // write the new cell.
        unsafe {
            let header = self.cell_header_at_offset(offset);
            header.write(cell.header);

            let mut content =
                NonNull::slice_from_raw_parts(header.add(1).cast(), cell.header.size as _);

            content.as_mut().copy_from_slice(&cell.content);
        }

        // Update header.
        self.header_mut().last_used_offset = offset;
        self.header_mut().free_space -= cell_storage_size;

        // Add new slot.
        self.header_mut().num_slots += 1;

        // If the index is not the last one, shift slots to the right.
        if index < self.header().num_slots {
            let end = self.header().num_slots as usize - 1;
            self.slot_array_mut()
                .copy_within(index as usize..end, index as usize + 1);
        }

        // Set offset.
        self.slot_array_mut()[index as usize] = offset;

        Ok(index)
    }

    /// Tries to replace the cell pointed by the given slot `index` with the
    /// `new_cell`.
    ///
    /// Similar to [`Self::try_insert`] there are 2 main cases:
    ///
    /// - Case 1: The new cell fits in the same place as the old cell:
    ///
    /// ```text
    ///                               The size of the new cell is less or
    ///                                  equal to that of the old cell
    ///
    ///                                         +----------+
    ///                                         | NEW CELL |
    ///                                         +----------+
    ///                                               |
    ///                                               v
    ///  +------+----+----+------------------+----------------+--------+--------+
    ///  |      | O3 | O1 | ->            <- |     CELL 3     |   DEL  | CELL 1 |
    ///  +------+----+----+------------------+----------------+--------+--------+
    /// ```
    ///
    /// - Case 2: The new cell does not fit in the same place, but it does fit
    /// in the page if we remove the old cell.
    ///     - Case A: The new cell fits in the "free space".
    ///     - Case B: We have to defragment the page to fit the new cell.
    ///
    /// ```text
    ///                                                    The size of the new cell is greater
    ///                                                         than that of the old cell
    ///
    ///                                                          +--------------------+
    ///                                                          |      NEW CELL      |
    ///                Case A: new cell fits here                +--------------------+
    ///                             |                                       |
    ///                             v                                       v
    ///  +------+----+----+------------------+----------------+--------+--------+
    ///  |      | O3 | O1 | ->            <- |      CELL 3    |   DEL  | CELL 1 |
    ///  +------+----+----+------------------+----------------+--------+--------+
    ///                             ^                              ^        ^
    ///                             |                              |        |
    ///                             +------------------------------+--------+
    ///                                                  |
    ///                                   Case B: new cell fits in the page
    ///                                   using all the available free space
    ///                                   including the deleted cell
    /// ```
    fn try_replace(&mut self, index: SlotId, new_cell: Box<Cell>) -> Result<Box<Cell>, Box<Cell>> {
        let old_cell = self.cell(index);

        // There's no way we can fit the new cell in this page, even if we
        // remove the one that has to be replaced.
        if self.header().free_space + old_cell.total_size() < new_cell.total_size() {
            return Err(new_cell);
        }

        // Case 1: The new cell is smaller than the old cell. This is the best
        // case scenario because we can simply overwrite the contents without
        // doing much else.
        if new_cell.header.size <= old_cell.header.size {
            // If new_cell is smaller we gain some extra bytes.
            let free_bytes = old_cell.header.size - new_cell.header.size;

            // Copy the old cell to return it.
            let owned_cell = self.owned_cell(index);

            // Overwrite the contents of the old cell.
            let old_cell = self.cell_mut(index);
            old_cell.content[..new_cell.content.len()].copy_from_slice(&new_cell.content);
            old_cell.header = new_cell.header;

            self.header_mut().free_space += free_bytes;

            return Ok(owned_cell);
        }

        // Case 2: The new cell fits in this page but we have to remove the old
        // one and potentially defragment the page. Worst case scenario.
        let old = self.remove(index);

        self.try_insert(index, new_cell)
            .expect("we made room for the new cell, it should fit in the page");

        Ok(old)
    }

    /// Removes the cell pointed by the given slot `index`.
    ///
    /// Unlike [`Self::try_insert`] and [`Self::try_replace`], this function
    /// cannot fail. However, it does panic if the given `index` is out of
    /// bounds or the page is overflow.
    pub fn remove(&mut self, index: SlotId) -> Box<Cell> {
        debug_assert!(
            !self.is_overflow(),
            "remove() does not handle overflow indexes"
        );

        let len = self.header().num_slots;

        assert!(index < len, "index {index} out of range for length {len}");

        let cell = self.owned_cell(index);

        // Remove the index as if we removed from a Vec.
        self.slot_array_mut()
            .copy_within(index as usize + 1..len as usize, index as usize);

        // Add new free space.
        self.header_mut().free_space += cell.total_size();

        // Decrease length.
        self.header_mut().num_slots -= 1;

        // Removed one slot, gained 2 extra bytes.
        self.header_mut().free_space += SLOT_SIZE;

        cell
    }

    /// Slides cells towards the right to eliminate fragmentation.
    ///
    /// For example:
    ///
    /// ```text
    ///   HEADER   SLOT ARRAY    FREE SPACE                      CELLS
    ///  +------+----+----+----+------------+--------+---------+--------+---------+--------+
    ///  |      | O1 | O2 | O3 | ->      <- | CELL 3 |   DEL   | CELL 2 |   DEL   | CELL 1 |
    ///  +------+----+----+----+------------+--------+---------+--------+---------+--------+
    /// ```
    ///
    /// turns into:
    ///
    /// ```text
    ///   HEADER   SLOT ARRAY              FREE SPACE                       CELLS
    ///  +------+----+----+----+--------------------------------+--------+--------+--------+
    ///  |      | O1 | O2 | O3 | ->                          <- | CELL 3 | CELL 2 | CELL 1 |
    ///  +------+----+----+----+--------------------------------+--------+--------+--------+
    /// ```
    ///
    /// Note that we the total amount of "free space" does not change. Instead,
    /// all the free space is now contiguous, but we do not gain any bytes from
    /// this.
    ///
    /// # Algorithm
    ///
    /// We can eliminate fragmentation in-place (without copying the page) by
    /// simply moving the cells that have the largest offset first. In the
    /// figures above, we would move CELL 1, then CELL 2 and finally CELL 3.
    /// This makes sure that we don't write one cell on top of another or we
    /// corrupt the data otherwise.
    fn defragment(&mut self) {
        let mut offsets = BinaryHeap::from_iter(
            self.slot_array()
                .iter()
                .enumerate()
                .map(|(i, offset)| (*offset, i)),
        );

        let mut destination_offset = self.size() - PAGE_HEADER_SIZE as usize;

        while let Some((offset, i)) = offsets.pop() {
            // SAFETY: Calling [`Self::cell_at_offset`] is safe here because we
            // obtained all the offsets from the slot array, which should always
            // be in a valid state. If that holds true, then casting the
            // dereferencing the cell pointer should be safe as well.
            unsafe {
                let cell = self.cell_at_offset(offset);
                let size = cell.as_ref().total_size() as usize;

                destination_offset -= size;

                cell.cast::<u8>().copy_to(
                    self.buffer
                        .content
                        .byte_add(destination_offset)
                        .cast::<u8>(),
                    size,
                );
            }
            self.slot_array_mut()[i] = destination_offset as u16;
        }

        self.header_mut().last_used_offset = destination_offset as u16;
    }

    /// Works like [`Vec::drain`] execept it doesn't remove elements unless
    /// consumed.
    ///
    /// Removes the specified cells from this page and returns an owned version
    /// of them. This function does account for [`Self::is_overflow`], so it's
    /// safe to call on overflow pages.
    pub fn drain(
        &mut self,
        range: impl RangeBounds<usize>,
    ) -> impl Iterator<Item = Box<Cell>> + '_ {
        let start = match range.start_bound() {
            Bound::Unbounded => 0,
            Bound::Excluded(i) => i + 1,
            Bound::Included(i) => *i,
        };

        let end = match range.end_bound() {
            Bound::Unbounded => self.len() as usize,
            Bound::Excluded(i) => *i,
            Bound::Included(i) => i + 1,
        };

        let mut drain_index = start;
        let mut slot_index = start;

        iter::from_fn(move || {
            // Copy cells until we reach the end.
            if drain_index < end {
                let cell = self
                    .overflow
                    .remove(&(drain_index as u16))
                    .unwrap_or_else(|| {
                        let cell = self.owned_cell(slot_index as _);
                        slot_index += 1;
                        cell
                    });

                drain_index += 1;

                Some(cell)
            } else {
                // Now compute gained space and shift slots towards the left.
                self.header_mut().free_space += (start..slot_index)
                    .map(|slot| self.cell(slot as _).storage_size())
                    .sum::<u16>();

                self.slot_array_mut().copy_within(slot_index.., start);

                self.header_mut().num_slots -= (slot_index - start) as u16;

                None
            }
        })
    }
}

impl Debug for Page {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        f.debug_struct("Page")
            .field("overflow", &self.overflow)
            .field("size", &self.size())
            .field("header", self.header())
            .field("slots", &self.slot_array())
            .field_with("cells", |f| {
                let mut list = f.debug_list();
                (0..self.header().num_slots).for_each(|slot| {
                    let cell = self.cell(slot);
                    let offset = self.slot_array()[slot as usize];
                    list.entry_with(|f| {
                        f.debug_struct("Cell")
                            .field("start", &offset)
                            .field("end", &(offset + cell.total_size()))
                            .field("size", &cell.header.size)
                            .field("header", &cell.header)
                            .field("content", &&cell.content)
                            .finish()
                    });
                });

                list.finish()
            })
            .finish()
    }
}

/// Header of an overflow page.
#[derive(Debug, PartialEq, Clone, Copy)]
#[repr(C)]
pub(crate) struct OverflowPageHeader {
    /// Next overflow page.
    pub next: PageNumber,
    /// Number of bytes stored in this page. Not to be confused with the page
    /// size.
    pub num_bytes: u16,
    /// See [`PageHeader::padding`] for details. Basically we need this because
    /// Miri.
    padding: u16,
}

/// Cell overflow page.
///
/// Cells have a maximum size that depends on the page size. See
/// [`Page::ideal_max_payload_size`] for details. However, when the payload size
/// of a cell exceeds the maximum size, we need to allocate extra pages to store
/// the contents of that cell. The cell then points to the first overflow page,
/// and that page points to the next and so on.
///
/// ```text
/// PAGE       SLOT          FREE
/// HEADER     ARRAY         SPACE         CELLS
/// +----------------------------------------------------------------+
/// | PAGE   | +---+                      +--------+---------+-----+ |
/// | HEADER | | 1 | ->                <- | HEADER | PAYLOAD | OVF | |
/// |        | +---+                      +--------+---------+--|--+ |
/// +------------|----------------------------------------------|----+
///              |                        ^                     |
///              |                        |                     |
///              +------------------------+                     |
///                                                             |
///      +------------------------------------------------------+
///      |
///      V
/// +--------------------+-------------------------------------------+
/// | +----------------+ | +---------------------------------------+ |
/// | | next | n_bytes | | |    OVERFLOW PAYLOAD (FULL PAGE)       | |
/// | +--|---+---------+ | +---------------------------------------+ |
/// +----|---------------+-------------------------------------------+
///      |
///      V
/// +--------------------+-------------------------------------------+
/// | +----------------+ | +------------------------+                |
/// | | next | n_bytes | | | REMAINING OVF PAYLOAD  |                |
/// | +------+---------+ | +------------------------+                |
/// +--------------------+-------------------------------------------+
/// OVERFLOW PAGE                  OVERFLOW PAGE CONTENT
/// HEADER                    (stores as many bytes as needed)
/// ```
///
/// When a [`CellHeader::is_overflow`] equals `true` then the last 4 bytes of
/// the [`Cell`] payload point to the first overflow page.
#[derive(Debug, PartialEq, Clone)]
pub(crate) struct OverflowPage {
    /// In-memory page buffer.
    buffer: BufferWithHeader<OverflowPageHeader>,
}

/// We can reuse the overflow page to represent free pages since we only need
/// a linked list of pages.
pub(crate) type FreePage = OverflowPage;

impl AsRef<[u8]> for OverflowPage {
    fn as_ref(&self) -> &[u8] {
        self.buffer.as_ref()
    }
}

impl AsMut<[u8]> for OverflowPage {
    fn as_mut(&mut self) -> &mut [u8] {
        self.buffer.as_mut()
    }
}

impl<H> From<BufferWithHeader<H>> for OverflowPage {
    fn from(buffer: BufferWithHeader<H>) -> Self {
        let mut buffer = buffer.cast();

        *buffer.header_mut() = OverflowPageHeader {
            next: 0,
            num_bytes: 0,
            padding: 0,
        };

        Self { buffer }
    }
}

impl OverflowPage {
    pub fn alloc(size: usize) -> Self {
        Self::from(BufferWithHeader::<OverflowPageHeader>::for_page(size))
    }

    /// Total space that can be used for overflow payloads.
    pub fn usable_space(page_size: usize) -> u16 {
        BufferWithHeader::<OverflowPageHeader>::usable_space(page_size)
    }

    /// Returns a reference to the header.
    pub fn header(&self) -> &OverflowPageHeader {
        self.buffer.header()
    }

    /// Returns a mutable reference to the header.
    pub fn header_mut(&mut self) -> &mut OverflowPageHeader {
        self.buffer.header_mut()
    }

    /// Returns a mutable reference to the entire content buffer.
    pub fn content_mut(&mut self) -> &mut [u8] {
        self.buffer.content_mut()
    }

    /// Returns a read-only reference to the payload (not the entire content).
    pub fn payload(&self) -> &[u8] {
        &self.buffer.content()[..self.header().num_bytes as usize]
    }
}

/// Database file header.
///
/// This is located at the beginning of the DB file and is used by the pager to
/// keep track of free pages and other metadata.
#[derive(Debug, Clone, Copy, PartialEq)]
#[repr(C, align(8))]
pub(crate) struct DbHeader {
    /// Magic number at the beginning of the file.
    pub magic: u32,
    /// Page size used for this DB file.
    pub page_size: u32,
    /// Number of pages in the file (both free and used).
    pub total_pages: u32,
    /// Number of free pages.
    pub free_pages: u32,
    /// First free page in the freelist.
    pub first_free_page: PageNumber,
    /// Last free page in the freelist.
    pub last_free_page: PageNumber,
}

/// The first page of the DB file (offset 0) is a special case since it contains
/// an additional header with metadata.
///
/// As such, this page has less usable space for [`Cell`] instances. Note that
/// the BTree balancing algorithm should always operate on pages of the same
/// size, but since root nodes are special cases this particular page doesn't
/// introduce any bugs. The alternative would be to use an entire page to store
/// just the [`DbHeader`], which doesn't make much sense if we peek a reasonable
/// page size of 4096 or above.
#[derive(Debug, PartialEq, Clone)]
pub(crate) struct PageZero {
    /// Page buffer.
    buffer: ManuallyDrop<BufferWithHeader<DbHeader>>,
    /// Inner BTree slotted page.
    page: ManuallyDrop<Page>,
}

impl<H> From<BufferWithHeader<H>> for PageZero {
    fn from(buffer: BufferWithHeader<H>) -> Self {
        let mut buffer = ManuallyDrop::new(buffer.cast());

        *buffer.header_mut() = DbHeader {
            magic: MAGIC,
            page_size: buffer.size as u32,
            total_pages: 1,
            free_pages: 0,
            first_free_page: 0,
            last_free_page: 0,
        };

        // SAFETY: `BufferWithHeader::from_non_null` requires 2 main guarantees
        // for wrapped buffers which we meet as follows:
        //
        // 1. The [`Drop`] implementation of the inner buffer will never run
        // because `self.page` is contained within [`ManuallyDrop`] and we
        // control exactly how the destructors run.
        //
        // 2. We don't use the inner buffer after the main allocated one is
        // dropped. At least not in this struct, externally though it's
        // possible to destructure [`PageZero`], move out of all its fields and
        // attempt to use `self.page` after `self.buffer` is dropped, but... why
        // would anyone do that? The buffer is wrapped in [`ManuallyDrop`] in
        // case we forget about this detail and fall into the trap.
        // [`ManuallyDrop`] delegates the responsibility again to whichever
        // function moves out of [`PageZero`].
        let page_buffer = unsafe {
            let page_buffer = BufferWithHeader::from_non_null(buffer.content);

            page_buffer
                .header
                .write(PageHeader::new(buffer.size - mem::size_of::<DbHeader>()));

            page_buffer
        };

        let page = ManuallyDrop::new(Page {
            buffer: page_buffer,
            overflow: HashMap::new(),
        });

        Self { buffer, page }
    }
}

impl PageZero {
    /// Creates a new page in memory.
    pub fn alloc(size: usize) -> Self {
        Self::from(BufferWithHeader::<DbHeader>::for_page(size))
    }

    /// Drops all the metadata and returns the inner buffer.
    fn into_buffer(mut self) -> BufferWithHeader<DbHeader> {
        // SAFETY: Neither the `ManuallyDrop` nor the `Page` will be used again
        // after this.
        let Page {
            buffer, overflow, ..
        } = unsafe { ManuallyDrop::take(&mut self.page) };

        mem::forget(buffer);
        mem::drop(overflow);

        // SAFETY: The `ManuallyDrop` won't be used again after this. The
        // inner buffer is safe to use if it was correctly allocated to begin
        // with.
        let buffer = unsafe { ManuallyDrop::take(&mut self.buffer) };
        mem::forget(self);

        buffer
    }

    /// Read-only reference to the database file header.
    pub fn header(&self) -> &DbHeader {
        self.buffer.header()
    }

    /// Mutable reference to the database file header.
    pub fn header_mut(&mut self) -> &mut DbHeader {
        self.buffer.header_mut()
    }

    /// Read-only references to the contained slotted page.
    pub fn as_btree_page(&self) -> &Page {
        &self.page
    }

    /// Mutable reference to the inner slotted page.
    pub fn as_btree_page_mut(&mut self) -> &mut Page {
        &mut self.page
    }
}

impl Drop for PageZero {
    fn drop(&mut self) {
        unsafe { drop(ptr::from_mut(self).read().into_buffer()) }
    }
}

impl AsRef<[u8]> for PageZero {
    fn as_ref(&self) -> &[u8] {
        self.buffer.as_ref()
    }
}

impl AsMut<[u8]> for PageZero {
    fn as_mut(&mut self) -> &mut [u8] {
        self.buffer.as_mut()
    }
}

/// Serves as a wrapper to hold multiple types of pages.
///
/// See [`crate::paging::pager::Pager::get_as`] for details as to why we need
/// this.
#[derive(Debug, PartialEq, Clone)]
pub(crate) enum MemPage {
    Zero(PageZero),
    Overflow(OverflowPage),
    Btree(Page),
}

/// See [`crate::paging::pager::Pager::get_as`]
pub(crate) trait PageTypeConversion = From<BufferWithHeader<PageHeader>>
    + From<BufferWithHeader<OverflowPageHeader>>
    + From<BufferWithHeader<DbHeader>>
    + Into<MemPage>;

impl MemPage {
    /// Allocates a dummy page in memory.
    ///
    /// Used by the [`crate::paging::cache`] module to fill up the buffer pool.
    /// [`Self::reinit_as`] can be used to convert the type to a different one
    /// reusing the same allocation, so it doesn't matter what type we choose
    /// here. We're choosing the most common type.
    pub fn alloc(size: usize) -> Self {
        MemPage::Btree(Page::alloc(size))
    }

    /// Converts this page into another type.
    ///
    /// This is not only a "conversion" but also a "reinitialization" since
    /// it drops all the metadata of the old type and reuses only its page
    /// buffer to initialize the new type.
    ///
    /// Basically we need this to reuse allocated buffers because it doesn't
    /// make sense to allocate a new buffer every single time we want to create
    /// a page if we already have a giant cache of pages.
    pub fn reinit_as<P: PageTypeConversion>(&mut self) {
        // SAFETY: We basically move out of self temporarily to create the new
        // type and then write the new variant back. If we already have mutable
        // access to self this should be "safe". At this point I already hate
        // the word "safe".
        unsafe {
            let mem_page = ptr::from_mut(self);

            let converted = match mem_page.read() {
                Self::Zero(zero) => P::from(zero.into_buffer()),
                Self::Overflow(overflow) => P::from(overflow.buffer),
                Self::Btree(page) => P::from(page.buffer),
            };

            mem_page.write(converted.into())
        }
    }

    /// Returns `true` if the page is in overflow state.
    pub fn is_overflow(&self) -> bool {
        match self {
            Self::Btree(page) => page.is_overflow(),
            Self::Zero(page_zero) => page_zero.as_btree_page().is_overflow(),
            _ => false,
        }
    }
}

impl AsRef<[u8]> for MemPage {
    fn as_ref(&self) -> &[u8] {
        match self {
            Self::Zero(page) => page.as_ref(),
            Self::Overflow(page) => page.as_ref(),
            Self::Btree(page) => page.as_ref(),
        }
    }
}

impl AsMut<[u8]> for MemPage {
    fn as_mut(&mut self) -> &mut [u8] {
        match self {
            Self::Zero(page) => page.as_mut(),
            Self::Overflow(page) => page.as_mut(),
            Self::Btree(page) => page.as_mut(),
        }
    }
}

impl From<Page> for MemPage {
    fn from(page: Page) -> MemPage {
        MemPage::Btree(page)
    }
}

impl From<OverflowPage> for MemPage {
    fn from(page: OverflowPage) -> MemPage {
        MemPage::Overflow(page)
    }
}

impl From<PageZero> for MemPage {
    fn from(page: PageZero) -> MemPage {
        MemPage::Zero(page)
    }
}

/// WARNING: Verbose duplicated garbage code ahead.
/// See [`crate::paging::pager::Pager::get_as`] for details.
/// We should probably use a macro to generate this but there are only 3 types
/// of pages for now so it's not that bad (still pretty bad).

impl<'p> TryFrom<&'p MemPage> for &'p Page {
    type Error = String;

    fn try_from(mem_page: &'p MemPage) -> Result<Self, Self::Error> {
        match mem_page {
            MemPage::Btree(page) => Ok(page),
            MemPage::Zero(page_zero) => Ok(page_zero.as_btree_page()),
            other => Err(format!("attempt to convert {other:?} into Page")),
        }
    }
}

impl<'p> TryFrom<&'p mut MemPage> for &'p mut Page {
    type Error = String;

    fn try_from(mem_page: &'p mut MemPage) -> Result<Self, Self::Error> {
        match mem_page {
            MemPage::Btree(page) => Ok(page),
            MemPage::Zero(page_zero) => Ok(page_zero.as_btree_page_mut()),
            other => Err(format!("attempt to convert {other:?} into Page")),
        }
    }
}

impl<'p> TryFrom<&'p MemPage> for &'p PageZero {
    type Error = String;

    fn try_from(mem_page: &'p MemPage) -> Result<Self, Self::Error> {
        match mem_page {
            MemPage::Zero(page_zero) => Ok(page_zero),
            other => Err(format!("attempt to convert {other:?} into PageZero")),
        }
    }
}

impl<'p> TryFrom<&'p mut MemPage> for &'p mut PageZero {
    type Error = String;

    fn try_from(mem_page: &'p mut MemPage) -> Result<Self, Self::Error> {
        match mem_page {
            MemPage::Zero(page_zero) => Ok(page_zero),
            other => Err(format!("attempt to convert {other:?} into PageZero")),
        }
    }
}

impl<'p> TryFrom<&'p MemPage> for &'p OverflowPage {
    type Error = String;

    fn try_from(mem_page: &'p MemPage) -> Result<Self, Self::Error> {
        match mem_page {
            MemPage::Overflow(page) => Ok(page),
            other => Err(format!("attempt to convert {other:?} into OverflowPage")),
        }
    }
}

impl<'p> TryFrom<&'p mut MemPage> for &'p mut OverflowPage {
    type Error = String;

    fn try_from(mem_page: &'p mut MemPage) -> Result<Self, Self::Error> {
        match mem_page {
            MemPage::Overflow(page) => Ok(page),
            other => Err(format!("attempt to convert {other:?} into OverflowPage")),
        }
    }
}

#[cfg(test)]
mod tests {
    use std::slice;

    use super::*;

    /// Returns a list of variable size cells.
    fn variable_size_cells(sizes: &[usize]) -> Vec<Box<Cell>> {
        sizes
            .iter()
            .enumerate()
            .map(|(i, size)| Cell::new(vec![i as u8 + 1; *size]))
            .collect()
    }

    /// Returns a list of `amount` cells each carrying `size` bytes of payload.
    fn fixed_size_cells(size: usize, amount: usize) -> Vec<Box<Cell>> {
        variable_size_cells(&vec![size; amount])
    }

    /// Returns the optimal page size to fit the given cells.
    ///
    /// Note that after inserting all the cells in the page, the page might
    /// still contain some free bytes because we must align to
    /// [`CELL_ALIGNMENT`].
    fn optimal_page_size_to_fit(cells: &[Box<Cell>]) -> usize {
        let size = PAGE_HEADER_SIZE + cells.iter().map(|cell| cell.storage_size()).sum::<u16>();

        Layout::from_size_align(size as usize, CELL_ALIGNMENT)
            .unwrap()
            .pad_to_align()
            .size()
    }

    /// Page builder for tests.
    struct Builder {
        size: Option<usize>,
        cells: Vec<Box<Cell>>,
    }

    impl Builder {
        fn new() -> Self {
            Self {
                size: None,
                cells: Vec::new(),
            }
        }

        fn size(mut self, size: usize) -> Self {
            self.size = Some(size);
            self
        }

        fn cells(mut self, cells: Vec<Box<Cell>>) -> Self {
            self.cells = cells;
            self
        }

        fn build(self) -> (Page, Vec<Box<Cell>>) {
            let size = self.size.unwrap_or(optimal_page_size_to_fit(&self.cells));

            let mut page = Page::alloc(size);
            page.push_all(self.cells.clone());

            (page, self.cells)
        }
    }

    impl Page {
        fn push_all(&mut self, cells: Vec<Box<Cell>>) {
            cells.into_iter().for_each(|cell| self.push(cell));
        }

        fn builder() -> Builder {
            Builder::new()
        }
    }

    /// # Arguments
    ///
    /// * `page` - [`Page`] instance.
    ///
    /// * `cells` - List of cells that have been inserted in the page
    /// (in order). Necessary for checking data corruption.
    fn assert_eq_cells_consecutive_offsets(page: &Page, cells: &[Box<Cell>]) {
        assert_eq_cells(page, cells);

        let mut expected_offset = page.size() - PAGE_HEADER_SIZE as usize;
        for (i, cell) in cells.iter().enumerate() {
            expected_offset -= cell.total_size() as usize;
            assert_eq!(
                page.slot_array()[i],
                expected_offset as u16,
                "offset mismatch for cell at index {i}: {cell:?}"
            );
        }
    }

    /// Checks that the page contains all the given cells.
    ///
    /// The order of the cells must be the same as the one in the page.
    fn assert_eq_cells(page: &Page, cells: &[Box<Cell>]) {
        assert_eq!(
            page.header().num_slots,
            cells.len() as u16,
            "length of slot array does not match length of inserted cells"
        );

        assert_free_space_matches_inserted_cells(page, cells);

        for (i, cell) in cells.iter().enumerate() {
            assert_eq!(
                page.cell(i as _),
                cell.as_ref(),
                "data for cell at index {i} is corrupted or otherwise bugged"
            );
        }
    }

    /// Computes the expected free space after inserting the given cells and
    /// checks that the page has that amount of free space.
    fn assert_free_space_matches_inserted_cells(page: &Page, cells: &[Box<Cell>]) {
        let used_space =
            PAGE_HEADER_SIZE + cells.iter().map(|cell| cell.storage_size()).sum::<u16>();
        let expected_free_space = page.size() - used_space as usize;

        assert_eq!(
            page.header().free_space,
            expected_free_space as u16,
            "page of size {} should contain {expected_free_space} bytes of free space after inserting paylods of sizes {:?}",
            page.size(),
            cells.iter().map(|cell| cell.header.size).collect::<Vec<_>>(),
        );
    }

    /// Simple test to check whether allocations and reads/writes work.
    #[test]
    fn buffer_with_header() {
        const HEADER_SIZE: usize = mem::size_of::<OverflowPageHeader>();
        const CONTENT_SIZE: usize = 24;
        const TOTAL_SIZE: usize = HEADER_SIZE + CONTENT_SIZE;

        let mut buf = BufferWithHeader::<OverflowPageHeader>::new(TOTAL_SIZE);

        let header = OverflowPageHeader {
            next: 10,
            num_bytes: CONTENT_SIZE as u16,
            padding: 0,
        };

        let content_byte = 0b10101010; // 170 in decimal

        *buf.header_mut() = header;
        buf.content_mut().fill(content_byte);

        let mut expected_buffer = [0; TOTAL_SIZE];
        expected_buffer[HEADER_SIZE..].fill(content_byte);

        unsafe {
            expected_buffer[..HEADER_SIZE].copy_from_slice(slice::from_raw_parts(
                ptr::from_ref(&header).cast(),
                HEADER_SIZE,
            ));
        };

        assert_eq!(buf.size, TOTAL_SIZE);
        assert_eq!(buf.header(), &header);
        assert_eq!(buf.content(), &[content_byte; CONTENT_SIZE]);
        assert_eq!(buf.as_slice(), &expected_buffer);
    }

    /// Insert 3 cells that carry 32 bytes of content (full size includes header
    /// and alignment).
    ///
    /// ```text
    ///  +--------+----+----+----+------+--------+--------+--------+
    ///  |   HDR  | O1 | O2 | O3 | FREE |   C3   |   C2   |   C1   |
    ///  +--------+----+----+----+------+--------+--------+--------+
    ///                                  32 bytes 32 bytes 32 bytes
    /// ```
    #[test]
    fn push_fixed_size_cells() {
        let (page, cells) = Page::builder().cells(fixed_size_cells(32, 3)).build();

        assert_eq_cells_consecutive_offsets(&page, &cells);
    }

    /// Insert 3 cells of different content size: 64, 32 and 80 bytes (full size
    /// includes header and alignment).
    ///
    /// ```text
    ///  +--------+----+----+----+------+-----------------+------+-----------+
    ///  |   HDR  | O1 | O2 | O3 | FREE |       C3        |  C2  |     C1    |
    ///  +--------+----+----+----+------+-----------------+------+-----------+
    ///                                      80 bytes     32 bytes  64 bytes
    /// ```
    #[test]
    fn push_variable_size_cells() {
        let (page, cells) = Page::builder()
            .cells(variable_size_cells(&[64, 32, 80]))
            .build();

        assert_eq_cells_consecutive_offsets(&page, &cells);
    }

    /// Delete slot number 1 from here:
    ///
    /// ```text
    ///  +--------+----+----+----+------+--------+--------+--------+
    ///  |   HDR  | O1 | O2 | O3 | FREE |   C3   |   C2   |   C1   |
    ///  +--------+----+----+----+------+--------+--------+--------+
    ///                                  32 bytes 32 bytes 32 bytes
    /// ```
    ///
    /// Result:
    ///
    /// ```text
    ///  +--------+----+----+-----------+--------+--------+--------+
    ///  |   HDR  | O1 | O3 |    FREE   |   C3   |  FREE  |   C1   |
    ///  +--------+----+----+-----------+--------+--------+--------+
    ///                                  32 bytes 32 bytes 32 bytes
    /// ```
    #[test]
    fn delete_slot() {
        let (mut page, mut cells) = Page::builder().cells(fixed_size_cells(32, 3)).build();

        let expected_offsets = [page.slot_array()[0], page.slot_array()[2]];

        page.remove(1);
        cells.remove(1);

        assert_eq!(page.slot_array(), expected_offsets);
        assert_eq_cells(&page, &cells);
    }

    /// Remove slot 1 from here:
    ///
    /// ```text
    ///  +--------+----+----+----+----+----+------+--+------------+------+----------+----+
    ///  |   HDR  | O1 | O2 | O3 | O4 | O5 | FREE |C5|     C4     |  C3  |    C2    | C1 |
    ///  +--------+----+----+----+----+----+------+--+------------+------+----------+----+
    ///                                            8       72        32       64      24
    ///                                          bytes    bytes     bytes    bytes   bytes
    /// ```
    ///
    /// Then remove slot 2 from this result:
    ///
    /// ```text
    ///  +--------+----+----+----+----+-----------+--+------------+------+----------+----+
    ///  |   HDR  | O1 | O3 | O4 | O5 |    FREE   |C5|     C4     |  C3  |   FREE   | C1 |
    ///  +--------+----+----+----+----+-----------+--+------------+------+----------+----+
    ///                                            8       72        32       64      24
    ///                                          bytes    bytes     bytes    bytes   bytes
    /// ```
    ///
    /// Now defragment this result:
    ///
    /// ```text
    ///  +--------+----+----+----+----------------+--+------------+------+----------+----+
    ///  |   HDR  | O1 | O3 | O5 |      FREE      |C5|    FREE    |  C3  |   FREE   | C1 |
    ///  +--------+----+----+----+----------------+--+------------+------+----------+----+
    ///                                  F         8       72        32       64      24
    ///                                          bytes    bytes     bytes    bytes   bytes
    /// ```
    ///
    /// Final result:
    ///
    /// ```text
    ///  +--------+----+----+----+----------------------------------------+--+------+----+
    ///  |   HDR  | O1 | O3 | O5 |                  FREE                  |C5|  C3  | C1 |
    ///  +--------+----+----+----+----------------------------------------+--+------+----+
    ///                                        F + 72 + 64 + 2H            8    32    24
    ///                                             bytes                bytes bytes bytes
    /// ```
    #[test]
    fn defragment() {
        let (mut page, mut cells) = Page::builder()
            .cells(variable_size_cells(&[24, 64, 32, 72, 8]))
            .build();

        for i in [1, 2] {
            page.remove(i as u16);
            cells.remove(i);
        }

        page.defragment();

        assert_eq_cells_consecutive_offsets(&page, &cells);
    }

    /// Create cells of unaligned size and insert them to check that padding
    /// is correct.
    #[test]
    fn unaligned_content() {
        let (page, cells) = Page::builder()
            .cells(variable_size_cells(&[7, 19, 20]))
            .build();

        assert_eq_cells_consecutive_offsets(&page, &cells);

        // Check padding
        for (i, cell) in cells.iter().enumerate() {
            assert_eq!(
                page.cell(i as u16).content.len(),
                Cell::aligned_size_of(&cell.content) as usize
            );
        }
    }

    /// Start with this page:
    ///
    /// ```text
    ///  +--------+----+----+----+----+------+----+--------+--------+--------+
    ///  |   HDR  | O1 | O2 | O3 | O4 | FREE | C4 |   C3   |   C2   |   C1   |
    ///  +--------+----+----+----+----+------+----+--------+--------+--------+
    ///                                        64     112      112      112
    ///                                       bytes  bytes    bytes    bytes
    /// ```
    ///
    /// Remove slot 1:
    ///
    /// ```text
    ///  +--------+----+----+----+-----------+----+--------+--------+--------+
    ///  |   HDR  | O1 | O3 | O4 |    FREE   | C4 |   C3   |  FREE  |   C1   |
    ///  +--------+----+----+----+-----------+----+--------+--------+--------+
    ///                              < 112     64     112      112      112
    ///                              bytes    bytes  bytes    bytes    bytes
    /// ```
    ///
    /// Inserting payload of size 112 should trigger auto-defragmentation:
    ///
    /// ```text
    ///  +--------+----+----+----+----+------+--------+----+--------+--------+
    ///  |   HDR  | O1 | O3 | O4 | O5 | FREE |   C5   | C4 |   C3   |   C1   |
    ///  +--------+----+----+----+----+------+--------+----+--------+--------+
    ///                                < 112     112    64     112      112
    ///                                bytes    bytes  bytes  bytes    bytes
    /// ```
    #[test]
    fn insert_defragmenting() {
        let (mut page, mut cells) = Page::builder()
            .cells(variable_size_cells(&[64, 112, 112, 112]))
            .build();

        page.remove(1);
        cells.remove(1);

        let new_cell = Cell::new(vec![4; 112]);

        cells.push(new_cell.clone());
        page.push(new_cell);

        assert_eq_cells_consecutive_offsets(&page, &cells);
    }

    /// Start with this page:
    ///
    /// ```text
    ///  +--------+----+----+----+------+-----------------+------+-----------+
    ///  |   HDR  | O1 | O2 | O3 | FREE |       C3        |  C2  |     C1    |
    ///  +--------+----+----+----+------+-----------------+------+-----------+
    ///                                     112 bytes     32 bytes  64 bytes
    /// ```
    ///
    /// Replace C2 with payload of same size C4:
    ///
    /// ```text
    ///  +--------+----+----+----+------+-----------------+------+-----------+
    ///  |   HDR  | O1 | O4 | O3 | FREE |       C3        |  C4  |     C1    |
    ///  +--------+----+----+----+------+-----------------+------+-----------+
    ///                                     112 bytes     32 bytes  64 bytes
    /// ```
    #[test]
    fn replace_cell_in_place() {
        let (mut page, mut cells) = Page::builder()
            .cells(variable_size_cells(&[64, 32, 112]))
            .build();

        let new_cell = Cell::new(vec![4; 32]);
        cells[1] = new_cell.clone();

        page.replace(1, new_cell);

        assert_eq_cells_consecutive_offsets(&page, &cells);
    }

    /// Start with this page:
    ///
    /// ```text
    ///  +--------+----+----+----------------------+---------------+-----------+
    ///  |   HDR  | O1 | O2 |         FREE         |      C2       |     C1    |
    ///  +--------+----+----+----------------------+---------------+-----------+
    ///                           >= 96 bytes           96 bytes      64 bytes
    /// ```
    ///
    /// Replace C1 with paylod C3 of size 96 bytes:
    ///
    /// ```text
    ///  +--------+----+----+------+---------------+---------------+-----------+
    ///  |   HDR  | O3 | O2 | FREE |      C3       |      C2       |   FREE    |
    ///  +--------+----+----+------+---------------+---------------+-----------+
    ///                                96 bytes         96 bytes      64 bytes
    /// ```
    #[test]
    fn replace_cell_removing_previous() {
        let (mut page, mut cells) = Page::builder()
            .size(optimal_page_size_to_fit(&variable_size_cells(&[
                64, 96, 96,
            ])))
            .cells(variable_size_cells(&[64, 96]))
            .build();

        let new_cell = Cell::new(vec![4; 96]);

        let expected_offset = page.size()
            - PAGE_HEADER_SIZE as usize
            - (cells.iter().map(|cell| cell.total_size()).sum::<u16>() + new_cell.total_size())
                as usize;

        cells[0] = new_cell.clone();

        page.replace(0, new_cell);

        assert_eq!(page.slot_array()[0], expected_offset as u16);
        assert_eq_cells(&page, &cells);
    }

    /// Check basic drain usage.
    #[test]
    fn drain() {
        let (mut page, mut cells) = Page::builder().cells(fixed_size_cells(32, 4)).build();

        let expected_offsets = [page.slot_array()[0], page.slot_array()[3]];

        assert_eq!(
            page.drain(1..=2).collect::<Vec<_>>(),
            cells.drain(1..=2).collect::<Vec<_>>()
        );

        assert_eq!(page.slot_array(), expected_offsets);
        assert_eq_cells(&page, &cells);
    }

    /// Inserts two cells more than the page can fit and then drains the
    /// entire page.
    ///
    /// This is the most important test here because this is what the BTree
    /// does when it runs the balancing algorithm.
    #[test]
    fn insert_with_overflow() {
        let (mut page, mut cells) = Page::builder().cells(fixed_size_cells(32, 3)).build();

        for i in [1, 3] {
            let new_cell = Cell::new(vec![(cells.len() + 1) as u8; 32]);
            cells.insert(i, new_cell.clone());
            page.insert(i as _, new_cell);
        }

        assert_eq!(page.overflow.len(), 2);
        assert_eq!(page.len() as usize, cells.len());
        assert_eq!(page.drain(..).collect::<Vec<_>>(), cells);
    }

    /// Mainly written to test the [`Drop`] impl for [`PageZero`] with Miri.
    #[test]
    fn page_zero() {
        let full_page_size = 512;
        let slotted_page_size = full_page_size - DB_HEADER_SIZE as usize;
        let min_cells = 4;
        let overflow_cells = min_cells + 2;
        let payload_size = Page::ideal_max_payload_size(slotted_page_size, min_cells) as usize;

        let mut page = PageZero::alloc(full_page_size);
        let mut cells = Vec::new();

        for i in 1..=overflow_cells {
            let cell = Cell::new(vec![i as u8; payload_size]);
            cells.push(cell.clone());
            page.as_btree_page_mut().push(cell);
        }

        assert_eq!(page.buffer.size, full_page_size);
        assert_eq!(page.as_btree_page().size(), slotted_page_size);
        assert!(page.as_btree_page().is_overflow());
        assert_eq!(page.as_btree_page().overflow.len(), 2);

        for (i, cell) in cells[..min_cells].iter().enumerate() {
            assert_eq!(page.as_btree_page().cell(i as u16), cell.as_ref());
        }

        // Use cargo miri test page::tests::page_zero to test the Drop impl
    }
}
