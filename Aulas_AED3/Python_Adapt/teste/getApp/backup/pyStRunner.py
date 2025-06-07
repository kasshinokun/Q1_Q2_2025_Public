import os 

# Command to execute
# Using Windows OS command
cmd1 = 'pip install shutil'
cmd2 = 'python -m streamlit run stHuffman.py'
cmd3 = 'python -m streamlit run stLZWPY.py'
cmd4 = 'python -m streamlit run getFromGitHub.py'
# Using os.system() method
choice_command = input("Please select process:\n1)Install lib\n2) Huffman\n3) LZW\n4) Downloader")
if choice_command == '1':
    os.system(cmd1)
elif choice_command == '2':
    os.system(cmd2)
elif choice_command == '3':
    os.system(cmd3)
elif choice_command == '4':
    os.system(cmd4)
else:
    print("Fail")
print("Done")

 
