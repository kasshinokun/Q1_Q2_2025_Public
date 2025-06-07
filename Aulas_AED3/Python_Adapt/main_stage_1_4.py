import os
import csv
import struct
import datetime
import heapq
import time
import hashlib
import getpass
import math
from math import ceil
from typing import List, Dict, Optional, Tuple, Union, DefaultDict, Deque
from collections import defaultdict, deque
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

# ==============================================
# Blowfish Implementation
# ==============================================
P_INIT = [
    0x243F6A88, 0x85A308D3, 0x13198A2E, 0x03707344, 0xA4093822, 0x299F31D0,
    0x082EFA98, 0xEC4E6C89, 0x452821E6, 0x38D01377, 0xBE5466CF, 0x34E90C6C,
    0xC0AC29B7, 0xC97C50DD, 0x3F84D5B5, 0xB5470917, 0x9216D5D9, 0x8979FB1B
]

S_INIT = [
    [
        0xD1310BA6, 0x98DFB5AC, 0x2FFD72DB, 0xD01ADFB7, 0xB8E1AFED, 0x6A267E96,
        0xBA7C9045, 0xF12C7F99, 0x24A19947, 0xB3916CF7, 0x0801F2E2, 0x858EFC16,
        0x636920D8, 0x71574E69, 0xA458FEA3, 0xF4933D7E, 0x0D95748F, 0x728EB658,
        0x718BCD58, 0x82154AEE, 0x7B54A41D, 0xC25A59B5, 0x9C30D539, 0x2AF26013,
        0xC5D1B023, 0x286085F0, 0xCA417918, 0xB8DB38EF, 0x8E79DCB0, 0x603A180E,
        0x6C9E0E8B, 0xB01E8A3E, 0xD71577C1, 0xBD314B27, 0x78AF2FDA, 0x55605C60,
        0xE65525F3, 0xAA55AB94, 0x57489862, 0x63E81440, 0x55CA396A, 0x2AAB10B6,
        0xB4CC5C34, 0x1141E8CE, 0xA15486AF, 0x7C72E993, 0xB3EE1411, 0x636FBC2A,
        0x2BA9C55D, 0x741831F6, 0xCE5C3E16, 0x9B87931E, 0xAFD6BA33, 0x6C24CF5C,
        0x7A325381, 0x28958677, 0x3B8F4898, 0x6B4BB9AF, 0xC4BFE81B, 0x66282193,
        0x61D809CC, 0xFB21A991, 0x487CAC60, 0x5DEC8032, 0xEF845D5D, 0xE98575B1,
        0xDC262302, 0xEB651B88, 0x23893E81, 0xD396ACC5, 0x0F6D6FF3, 0x83F44239,
        0x2E0B4482, 0xA4842004, 0x69C8F04A, 0x9E1F9B5E, 0x21C66842, 0xF6E96C9A,
        0x670C9C61, 0xABD388F0, 0x6A51A0D2, 0xD8542F68, 0x960FA728, 0xAB5133A3,
        0x6EEF0B6C, 0x137A3BE4, 0xBA3BF050, 0x7EFB2A98, 0xA1F1651D, 0x39AF0176,
        0x66CA593E, 0x82430E88, 0x8CEE8619, 0x456F9FB4, 0x7D84A5C3, 0x3B8B5EBE,
        0xE06F75D8, 0x85C12073, 0x401A449F, 0x56C16AA6, 0x4ED3AA62, 0x363F7706,
        0x1BFEDF72, 0x429B023D, 0x37D0D724, 0xD00A1248, 0xDB0FEAD3, 0x49F1C09B,
        0x075372C9, 0x80991B7B, 0x25D479D8, 0xF6E8DEF7, 0xE3FE501A, 0xB6794C3B,
        0x976CE0BD, 0x04C006BA, 0xC1A94FB6, 0x409F60C4, 0x5E5C9EC2, 0x196A2463,
        0x68FB6FAF, 0x3E6C53B5, 0x1339B2EB, 0x3B52EC6F, 0x6DFC511F, 0x9B30952C,
        0xCC814544, 0xAF5EBD09, 0xBEE3D004, 0xDE334AFD, 0x660F2807, 0x192E4BB3,
        0xC0CBA857, 0x45C8740F, 0xD20B5F39, 0xB9D3FBDB, 0x5579C0BD, 0x1A60320A,
        0xD6A100C6, 0x402C7279, 0x679F25FE, 0xFB1FA3CC, 0x8EA5E9F8, 0xDB3222F8,
        0x3C7516DF, 0xFD616B15, 0x2F501EC8, 0xAD0552AB, 0x323DB5FA, 0xFD238760,
        0x53317B48, 0x3E00DF82, 0x9E5C57BB, 0xCA6F8CA0, 0x1A87562E, 0xDF1769DB,
        0xD542A8F6, 0x287EFFC3, 0xAC6732C6, 0x8C4F5573, 0x695B27B0, 0xBBCA58C8,
        0xE1FFA35D, 0xB8F011A0, 0x10FA3D98, 0xFD2183B8, 0x4AFCB56C, 0x2DD1D35B,
        0x9A53E479, 0xB6F84565, 0xD28E49BC, 0x4BFB9790, 0xE1DDF2DA, 0xA4CB7E33,
        0x62FB1341, 0xCEE4C6E8, 0xEF20CADA, 0x36774C01, 0xD07E9EFE, 0x2BF11FB4,
        0x95DBDA4D, 0xAE909198, 0xEAAD8E71, 0x6B93D5A0, 0xD08ED1D0, 0xAFC725E0,
        0x8E3C5B2F, 0x8E7594B7, 0x8FF6E2FB, 0xF2122B64, 0x8888B812, 0x900DF01C,
        0x4FAD5EA0, 0x688FC31C, 0xD1CFF191, 0xB3A8C1AD, 0x2F2F2218, 0xBE0E1777,
        0xEA752DFE, 0x8B021FA1, 0xE5A0CC0F, 0xB56F74E8, 0x18ACF3D6, 0xCE89E299,
        0xB4A84FE0, 0xFD13E0B7, 0x7CC43B81, 0xD2ADA8D9, 0x165FA266, 0x80957705,
        0x93CC7314, 0x211A1477, 0xE6AD2065, 0x77B5FA86, 0xC75442F5, 0xFB9D35CF,
        0xEBCDAF0C, 0x7B3E89A0, 0xD6411BD3, 0xAE1E7E49, 0x00250E2D, 0x2071B35E,
        0x226800BB, 0x57B8E0AF, 0x2464369B, 0xF009B91E, 0x5563911D, 0x59DFA6AA,
        0x78C14389, 0xD95A537F, 0x207D5BA2, 0x02E5B9C5, 0x83260376, 0x6295CFA9,
        0x11C81968, 0x4E734A41, 0xB3472DCA, 0x7B14A94A, 0x1B510052, 0x9A532915,
        0xD60F573F, 0xBC9BC6E4, 0x2B60A476, 0x81E67400, 0x08BA6FB5, 0x571BE91F,
        0xF296EC6B, 0x2A0DD915, 0xB6636521, 0xE7B9F9B6, 0xFF34052E, 0xC5855664,
        0x53B02D5D, 0xA99F8FA1, 0x08BA4799, 0x6E85076A
    ],
    [
        0x4B7A70E9, 0xB5B32944, 0xDB75092E, 0xC4192623, 0xAD6EA6B0, 0x49A7DF7D,
        0x9CEE60B8, 0x8FEDB266, 0xECAA8C71, 0x699A17FF, 0x5664526C, 0xC2B19EE1,
        0x193602A5, 0x75094C29, 0xA0591340, 0xE4183A3E, 0x3F54989A, 0x5B429D65,
        0x6B8FE4D6, 0x99F73FD6, 0xA1D29C07, 0xEFE830F5, 0x4D2D38E6, 0xF0255DC1,
        0x4CDD2086, 0x8470EB26, 0x6382E9C6, 0x021ECC5E, 0x09686B3F, 0x3EBAEFC9,
        0x3C971814, 0x6B6A70A1, 0x687F3584, 0x52A0E286, 0xB79C5305, 0xAA500737,
        0x3E07841C, 0x7FDEAE5C, 0x8E7D44EC, 0x5716F2B8, 0xB03ADA37, 0xF0500C0D,
        0xF01C1F04, 0x0200B3FF, 0xAE0CF51A, 0x3CB574B2, 0x25837A58, 0xDC0921BD,
        0xD19113F9, 0x7CA92FF6, 0x94324773, 0x22F54701, 0x3AE5E581, 0x37C2DADC,
        0xC8B57634, 0x9AF3DDA7, 0xA9446146, 0x0FD0030E, 0xECC8C73E, 0xA4751E41,
        0xE238CD99, 0x3BEA0E2F, 0x3280BBA1, 0x183EB331, 0x4E548B38, 0x4F6DB908,
        0x6F420D03, 0xF60A04BF, 0x2CB81290, 0x24977C79, 0x5679B072, 0xBCAF89AF,
        0xDE9A771F, 0xD9930810, 0xB38BAE12, 0xDCCF3F2E, 0x5512721F, 0x2E6B7124,
        0x501ADDE6, 0x9F84CD87, 0x7A584718, 0x7408DA17, 0xBC9F9ABC, 0xE94B7D8C,
        0xEC7AEC3A, 0xDB851DFA, 0x63094366, 0xC464C3D2, 0xEF1C1847, 0x3215D908,
        0xDD433B37, 0x24C2BA16, 0x12A14D43, 0x2A65C451, 0x50940002, 0x133AE4DD,
        0x71DFF89E, 0x10314E55, 0x81AC77D6, 0x5F11199B, 0x043556F1, 0xD7A3C76B,
        0x3C11183B, 0x5924A509, 0xF28FE6ED, 0x97F1FBFA, 0x9EBABF2C, 0x1E153C6E,
        0x86E34570, 0xEAE96FB1, 0x860E5E0A, 0x5A3E2AB3, 0x771FE71C, 0x4E3D06FA,
        0x2965DCB9, 0x99E71D0F, 0x803E89D6, 0x5266C825, 0x2E4CC978, 0x9C10B36A,
        0xC6150EBA, 0x94E2EA78, 0xA5FC3C53, 0x1E0A2DF4, 0xF2F74EA7, 0x361D2B3D,
        0x1939260F, 0x19C27960, 0x5223A708, 0xF71312B6, 0xEBADFE6E, 0xEAC31F66,
        0xE3BC4595, 0xA67BC883, 0xB17F37D1, 0x018CFF28, 0xC332DDEF, 0xBE6C5AA5,
        0x65582185, 0x68AB9802, 0xEECEA50F, 0xDB2F953B, 0x2AEF7DAD, 0x5B6E2F84,
        0x1521B628, 0x29076170, 0xECDD4775, 0x619F1510, 0x13CCA830, 0xEB61BD96,
        0x0334FE1E, 0xAA0363CF, 0xB5735C90, 0x4C70A239, 0xD59E9E0B, 0xCBAADE14,
        0xEECC86BC, 0x60622CA7, 0x9CAB5CAB, 0xB2F3846E, 0x648B1EAF, 0x19BDF0CA,
        0xA02369B9, 0x655ABB50, 0x40685A32, 0x3C2AB4B3, 0x319EE9D5, 0xC021B8F7,
        0x9B540B19, 0x875FA099, 0x95F7997E, 0x623D7DA8, 0xF837889A, 0x97E32D77,
        0x11ED935F, 0x16681281, 0x0E358829, 0xC7E61FD6, 0x96DEDFA1, 0x7858BA99,
        0x57F584A5, 0x1B227263, 0x9B83C3FF, 0x1AC24696, 0xCDB30AEB, 0x532E3054,
        0x8FD948E4, 0x6DBC3128, 0x58EBF2EF, 0x34C6FFEA, 0xFE28ED61, 0xEE7C3C73,
        0x5D4A14D9, 0xE864B7E3, 0x42105D14, 0x203E13E0, 0x45EEE2B6, 0xA3AAABEA,
        0xDB6C4F15, 0xFACB4FD0, 0xC742F442, 0xEF6ABBB5, 0x654F3B1D, 0x41CD2105,
        0xD81E799E, 0x86854DC7, 0xE44B476A, 0x3D816250, 0xCF62A1F2, 0x5B8D2646,
        0xFC8883A0, 0xC1C7B6A3, 0x7F1524C3, 0x69CB7492, 0x47848A0B, 0x5692B285,
        0x095BBF00, 0xAD19489D, 0x1462B174, 0x23820E00, 0x58428D2A, 0x0C55F5EA,
        0x1DADF43E, 0x233F7061, 0x3372F092, 0x8D937E41, 0xD65FECF1, 0x6C223BDB,
        0x7CDE3759, 0xCBEE7460, 0x4085F2A7, 0xCE77326E, 0xA6078084, 0x19F8509E,
        0xE8EFD855, 0x61D99735, 0xA969A7AA, 0xC50C06C2, 0x5A04ABFC, 0x800BCADC,
        0x9E447A2E, 0xC3453484, 0xFDD56705, 0x0E1E9EC9, 0xDB73DBD3, 0x105588CD,
        0x675FDA79, 0xE3674340, 0xC5C43465, 0x713E38D8, 0x3D28F89E, 0xF16DFF20,
        0x153E21E7, 0x8FB03D4A, 0xE6E39F2B, 0xDB83ADF7
    ],
    [
        0xE93D5A68, 0x948140F7, 0xF64C261C, 0x94692934, 0x411520F7, 0x7602D4F7,
        0xBCF46B2E, 0xD4A20068, 0xD4082471, 0x3320F46A, 0x43B7D4B7, 0x500061AF,
        0x1E39F62E, 0x97244546, 0x14214F74, 0xBF8B8840, 0x4D95FC1D, 0x96B591AF,
        0x70F4DDD3, 0x66A02F45, 0xBFBC09EC, 0x03BD9785, 0x7FAC6DD0, 0x31CB8504,
        0x96EB27B3, 0x55FD3941, 0xDA2547E6, 0xABCA0A9A, 0x28507825, 0x530429F4,
        0x0A2C86DA, 0xE9B66DFB, 0x68DC1462, 0xD7486900, 0x680EC0A4, 0x27A18DEE,
        0x4F3FFEA2, 0xE887AD8C, 0xB58CE006, 0x7AF4D6B6, 0xAACE1E7C, 0xD3375FEC,
        0xCE78A399, 0x406B2A42, 0x20FE9E35, 0xD9F385B9, 0xEE39D7AB, 0x3B124E8B,
        0x1DC9FAF7, 0x4B6D1856, 0x26A36631, 0xEAE397B2, 0x3A6EFA74, 0xDD5B4332,
        0x6841E7F7, 0xCA7820FB, 0xFB0AF54E, 0xD8FEB397, 0x454056AC, 0xBA489527,
        0x55533A3A, 0x20838D87, 0xFE6BA9B7, 0xD096954B, 0x55A867BC, 0xA1159A58,
        0xCCA92963, 0x99E1DB33, 0xA62A4A56, 0x3F3125F9, 0x5EF47E1C, 0x9029317C,
        0xFDF8E802, 0x04272F70, 0x80BB155C, 0x05282CE3, 0x95C11548, 0xE4C66D22,
        0x48C1133F, 0xC70F86DC, 0x07F9C9EE, 0x41041F0F, 0x404779A4, 0x5D886E17,
        0x325F51EB, 0xD59BC0D1, 0xF2BCC18F, 0x41113564, 0x257B7834, 0x602A9C60,
        0xDFF8E8A3, 0x1F636C1B, 0x0E12B4C2, 0x02E1329E, 0xAF664FD1, 0xCAD18115,
        0x6B2395E0, 0x333E92E1, 0x3B240B62, 0xEEBEB922, 0x85B2A20E, 0xE6BA0D99,
        0xDE720C8C, 0x2DA2F728, 0xD0127845, 0x95B794FD, 0x647D0862, 0xE7CCF5F0,
        0x5449A36F, 0x877D48FA, 0xC39DFD27, 0xF33E8D1E, 0x0A476341, 0x992EFF74,
        0x3A6F6EAB, 0xF4F8FD37, 0xA812DC60, 0xA1EBDDF8, 0x991BE14C, 0xDB6E6B0D,
        0xC67B5510, 0x6D672C37, 0x2765D43B, 0xDCD0E804, 0xF1290DC7, 0xCC00FFA3,
        0xB5390F92, 0x690FED0B, 0x667B9FFB, 0xCEDB7D9C, 0xA091CF0B, 0xD9155EA3,
        0xBB132F88, 0x515BAD24, 0x7B9479BF, 0x763BD6EB, 0x37392EB3, 0xCC115979,
        0x8026E297, 0xF42E312D, 0x6842ADA7, 0xC66A2B3B, 0x12754CCC, 0x782EF11C,
        0x6A124237, 0xB79251E7, 0x06A1BBE6, 0x4BFB6350, 0x1A6B1018, 0x11CAEDFA,
        0x3D25BDD8, 0xE2E1C3C9, 0x44421659, 0x0A121386, 0xD90CEC6E, 0xD5ABEA2A,
        0x64AF674E, 0xDA86A85F, 0xBEBFE988, 0x64E4C3FE, 0x9DBC8057, 0xF0F7C086,
        0x60787BF8, 0x6003604D, 0xD1FD8346, 0xF6381FB0, 0x7745AE04, 0xD736FCCC,
        0x83426B33, 0xF01EAB71, 0xB0804187, 0x3C005E5F, 0x77A057BE, 0xBDE8AE24,
        0x55464299, 0xBF582E61, 0x4E58F48F, 0xF2DDFDA2, 0xF474EF38, 0x8789BDC2,
        0x5366F9C3, 0xC8B38E74, 0xB475F255, 0x46FCD9B9, 0x7AEB2661, 0x8B1DDF84,
        0x846A0E79, 0x915F95E2, 0x466E598E, 0x20B45770, 0x8CD55591, 0xC902DE4C,
        0xB90BACE1, 0xBB8205D0, 0x11A86248, 0x7574A99E, 0xB77F19B6, 0xE0A9DC09,
        0x662D09A1, 0xC4324633, 0xE85A1F02, 0x09F0BE8C, 0x4A99A025, 0x1D6EFE10,
        0x1AB93D1D, 0x0BA5A4DF, 0xA186F20F, 0x2868F169, 0xDCB7DA83, 0x573906FE,
        0xA1E2CE9B, 0x4FCD7F52, 0x50115E01, 0xA70683FA, 0xA002B5C4, 0x0DE6D027,
        0x9AF88C27, 0x773F8641, 0xC3604C06, 0x61A806B5, 0xF0177A28, 0xC0F586E0,
        0x006058AA, 0x30DC7D62, 0x11E69ED7, 0x2338EA63, 0x53C2DD94, 0xC2C21634,
        0xBBCBEE56, 0x90BCB6DE, 0xEBFC7DA1, 0xCE591D76, 0x6F05E409, 0x4B7C0188,
        0x39720A3D, 0x7C927C24, 0x86E3725F, 0x724D9DB9, 0x1AC15BB4, 0xD39EB8FC,
        0xED545578, 0x08FCA5B5, 0xD83D7CD3, 0x4DAD0FC4, 0x1E50EF5E, 0xB161E6F8,
        0xA28514D9, 0x6C51133C, 0x6FD5C7E7, 0x56E14EC4, 0x362ABFCE, 0xDDC6C837,
        0xD79A3234, 0x92638212, 0x670EFA8E, 0x406000E0
    ],
    [
        0x3A39CE37, 0xD3FAF5CF, 0xABC27737, 0x5AC52D1B, 0x5CB0679E, 0x4FA33742,
        0xD3822740, 0x99BC9BBE, 0xD5118E9D, 0xBF0F7315, 0xD62D1C7E, 0xC700C47B,
        0xB78C1B6B, 0x21A19045, 0xB26EB1BE, 0x6A366EB4, 0x5748AB2F, 0xBC946E79,
        0xC6A376D2, 0x6549C2C8, 0x530FF8EE, 0x468DDE7D, 0xD5730A1D, 0x4CD04DC6,
        0x2939BBDB, 0xA9BA4650, 0xAC9526E8, 0xBE5EE304, 0xA1FAD5F0, 0x6A2D519A,
        0x63EF8CE2, 0x9A86EE22, 0xC089C2B8, 0x43242EF6, 0xA51E03AA, 0x9CF2D0A4,
        0x83C061BA, 0x9BE96A4D, 0x8FE51550, 0xBA645BD6, 0x2826A2F9, 0xA73A3AE1,
        0x4BA99586, 0xEF5562E9, 0xC72FEFD3, 0xF752F7DA, 0x3F046F69, 0x77FA0A59,
        0x80E4A915, 0x87B08601, 0x9B09E6AD, 0x3B3EE593, 0xE990FD5A, 0x9E34D797,
        0x2CF0B7D9, 0x022B8B51, 0x96D5AC3A, 0x017DA67D, 0xD1CF3ED6, 0x7C7D2D28,
        0x1F9F25CF, 0xADF2B89B, 0x5AD6B472, 0x5A88F54C, 0xE029AC71, 0xE019A5E6,
        0x47B0ACFD, 0xED93FA9B, 0xE8D3C48D, 0x283B57CC, 0xF8D56629, 0x79132E28,
        0x785F0191, 0xED756055, 0xF7960E44, 0xE3D35E8C, 0x15056DD4, 0x88F46DBA,
        0x03A16125, 0x0564F0BD, 0xC3EB9E15, 0x3C9057A2, 0x97271AEC, 0xA93A072A,
        0x1B3F6D9B, 0x1E6321F5, 0xF59C66FB, 0x26DCF319, 0x7533D928, 0xB155FDF5,
        0x03563482, 0x8ABA3CBB, 0x28517711, 0xC20AD9F8, 0xABCC5167, 0xCCAD925F,
        0x4DE81751, 0x3830DC8E, 0x379D5862, 0x9320F991, 0xEA7A90C2, 0xFB3E7BCE,
        0x5121CE64, 0x774FBE32, 0xA8B6E37E, 0xC3293D46, 0x48DE5369, 0x6413E680,
        0xA2AE0810, 0xDD6DB224, 0x69852DFD, 0x09072166, 0xB39A460A, 0x6445C0DD,
        0x586CDECF, 0x1C20C8AE, 0x5BBEF7DD, 0x1B588D40, 0xCCD2017F, 0x6BB4E3BB,
        0xDDA26A7E, 0x3A59FF45, 0x3E350A44, 0xBCB4CDD5, 0x72EACEA8, 0xFA6484BB,
        0x8D6612AE, 0xBF3C6F47, 0xD29BE463, 0x542F5D9E, 0xAEC2771B, 0xF64E6370,
        0x740E0D8D, 0xE75B1357, 0xF8721671, 0xAF537D5D, 0x4040CB08, 0x4EB4E2CC,
        0x34D2466A, 0x0115AF84, 0xE1B00428, 0x95983A1D, 0x06B89FB4, 0xCE6EA048,
        0x6F3F3B82, 0x3520AB82, 0x011A1D4B, 0x277227F8, 0x611560B1, 0xE7933FDC,
        0xBB3A792B, 0x344525BD, 0xA08839E1, 0x51CE794B, 0x2F32C9B7, 0xA01FBAC9,
        0xE01CC87E, 0xBCC7D1F6, 0xCF0111C3, 0xA1E8AAC7, 0x1A908749, 0xD44FBD9A,
        0xD0DADECB, 0xD50ADA38, 0x0339C32A, 0xC6913667, 0x8DF9317C, 0xE0B12B4F,
        0xF79E59B7, 0x43F5BB3A, 0xF2D519FF, 0x27D9459C, 0xBF97222C, 0x15E6FC2A,
        0x0F91FC71, 0x9B941525, 0xFAE59361, 0xCEB69CEB, 0xC2A86459, 0x12BAA8D1,
        0xB6C1075E, 0xE3056A0C, 0x10D25065, 0xCB03A442, 0xE0EC6E0E, 0x1698DB3B,
        0x4C98A0BE, 0x3278E964, 0x9F1F9532, 0xE0D392DF, 0xD3A0342B, 0x8971F21E,
        0x1B0A7441, 0x4BA3348C, 0xC5BE7120, 0xC37632D8, 0xDF359F8D, 0x9B992F2E,
        0xE60B6F47, 0x0FE3F11D, 0xE54CDA54, 0x1EDAD891, 0xCE6279CF, 0xCD3E7E6F,
        0x1618B166, 0xFD2C1D05, 0x848FD2C5, 0xF6FB2299, 0xF523F357, 0xA6327623,
        0x93A83531, 0x56CCCD02, 0xACF08162, 0x5A75EBB5, 0x6E163697, 0x88D273CC,
        0xDE966292, 0x81B949D0, 0x4C50901B, 0x71C65614, 0xE6C6C7BD, 0x327A140A,
        0x45E1D006, 0xC3F27B9A, 0xC9AA53FD, 0x62A80F00, 0xBB25BFE2, 0x35BDD2F6,
        0x71126905, 0xB2040222, 0xB6CBCF7C, 0xCD769C2B, 0x53113EC0, 0x1640E3D3,
        0x38ABBD60, 0x2547ADF0, 0xBA38209C, 0xF746CE76, 0x77AFA1C5, 0x20756060,
        0x85CBFE4E, 0x8AE88DD8, 0x7AAAF9B0, 0x4CF9AA7E, 0x1948C25C, 0x02FB8A8C,
        0x01C36AE4, 0xD6EBE1F9, 0x90D4F869, 0xA65CDEA0, 0x3F09252D, 0xC208E69F,
        0xB74E6132, 0xCE77E25B, 0x578FDFE3, 0x3AC372E6
    ]
]

class Blowfish:
    def __init__(self, key):
        self.p_boxes = list(P_INIT)
        self.s_boxes = [list(box) for box in S_INIT]
        self._key_expansion(key)

    def _key_expansion(self, key):
        key_len = len(key)
        j = 0
        for i in range(18):
            data = 0
            for k in range(4):
                data = (data << 8) | key[j]
                j = (j + 1) % key_len
            self.p_boxes[i] ^= data
        
        l, r = 0, 0
        for i in range(0, 18, 2):
            l, r = self.encrypt_block(l, r)
            self.p_boxes[i] = l
            self.p_boxes[i+1] = r
        
        for i in range(4):
            for j in range(0, 256, 2):
                l, r = self.encrypt_block(l, r)
                self.s_boxes[i][j] = l
                self.s_boxes[i][j+1] = r

    def F(self, x):
        h = (self.s_boxes[0][x >> 24] + self.s_boxes[1][(x >> 16) & 0xFF]) & 0xFFFFFFFF
        return ((h ^ self.s_boxes[2][(x >> 8) & 0xFF]) + self.s_boxes[3][x & 0xFF]) & 0xFFFFFFFF

    def encrypt_block(self, left, right):
        for i in range(16):
            left ^= self.p_boxes[i]
            right ^= self.F(left)
            left, right = right, left
        left, right = right, left
        right ^= self.p_boxes[16]
        left ^= self.p_boxes[17]
        return left, right

    def decrypt_block(self, left, right):
        for i in range(17, 1, -1):
            left ^= self.p_boxes[i]
            right ^= self.F(left)
            left, right = right, left
        left, right = right, left
        right ^= self.p_boxes[1]
        left ^= self.p_boxes[0]
        return left, right

    def encrypt(self, data):
        if len(data) % 8 != 0:
            data = self._pkcs7_pad(data, 8)
        result = bytearray()
        for i in range(0, len(data), 8):
            block = data[i:i+8]
            left = int.from_bytes(block[:4], 'big')
            right = int.from_bytes(block[4:], 'big')
            l, r = self.encrypt_block(left, right)
            result.extend(l.to_bytes(4, 'big'))
            result.extend(r.to_bytes(4, 'big'))
        return bytes(result)

    def decrypt(self, data):
        result = bytearray()
        for i in range(0, len(data), 8):
            block = data[i:i+8]
            left = int.from_bytes(block[:4], 'big')
            right = int.from_bytes(block[4:], 'big')
            l, r = self.decrypt_block(left, right)
            result.extend(l.to_bytes(4, 'big'))
            result.extend(r.to_bytes(4, 'big'))
        return self._pkcs7_unpad(bytes(result))

    @staticmethod
    def _pkcs7_pad(data, block_size):
        pad_len = block_size - (len(data) % block_size)
        return data + bytes([pad_len] * pad_len)

    @staticmethod
    def _pkcs7_unpad(data):
        pad_len = data[-1]
        if pad_len < 1 or pad_len > len(data):
            raise ValueError("Invalid padding")
        if not all(b == pad_len for b in data[-pad_len:]):
            raise ValueError("Invalid padding bytes")
        return data[:-pad_len]

def derive_key(password, salt, dk_len=32, iterations=100000):
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, iterations, dk_len)

def encrypt_file(input_file, output_file, password):
    salt = os.urandom(16)
    key = derive_key(password, salt)
    
    cipher = Blowfish(key)
    with open(input_file, 'rb') as f:
        plaintext = f.read()
    
    ciphertext = cipher.encrypt(plaintext)
    
    with open(output_file, 'wb') as f:
        f.write(salt)
        f.write(ciphertext)

def decrypt_file(input_file, output_file, password):
    with open(input_file, 'rb') as f:
        salt = f.read(16)
        ciphertext = f.read()
    
    key = derive_key(password, salt)
    cipher = Blowfish(key)
    plaintext = cipher.decrypt(ciphertext)
    
    with open(output_file, 'wb') as f:
        f.write(plaintext)


# ==============================================
# Data Object Definition
# ==============================================
class DataObject:
    DATE_FORMAT = "%d/%m/%Y"
    
    def __init__(self, 
                 ID_registro: int = 0,
                 crash_date: str = "",
                 data: datetime.date=datetime.date.min,
                 traffic_control_device: str = "",
                 weather_condition: str = "",
                 lighting_condition: List[str] = [],
                 first_crash_type: str = "",
                 trafficway_type: str = "",
                 alignment: str = "",
                 roadway_surface_cond: str = "",
                 road_defect: str = "",
                 crash_type: List[str] = [],
                 intersection_related_i: bool = False,
                 damage: str = "",
                 prim_contributory_cause: str = "",
                 num_units: int = 0,
                 most_severe_injury: List[str] = [],
                 injuries_total: float = 0.0,
                 injuries_fatal: float = 0.0,
                 injuries_incapacitating: float = 0.0,
                 injuries_non_incapacitating: float = 0.0,
                 injuries_reported_not_evident: float = 0.0,
                 injuries_no_indication: float = 0.0,
                 crash_hour: int = 0,
                 crash_day_of_week: int = 0,
                 crash_month: int = 0):
        
        self.ID_registro = ID_registro
        self.crash_date = crash_date
        self.data = data or datetime.date(1900, 1, 1)
        self.traffic_control_device = traffic_control_device
        self.weather_condition = weather_condition
        self.lighting_condition = lighting_condition or []
        self.first_crash_type = first_crash_type
        self.trafficway_type = trafficway_type
        self.alignment = alignment
        self.roadway_surface_cond = roadway_surface_cond
        self.road_defect = road_defect
        self.crash_type = crash_type or []
        self.intersection_related_i = intersection_related_i
        self.damage = damage
        self.prim_contributory_cause = prim_contributory_cause
        self.num_units = num_units
        self.most_severe_injury = most_severe_injury or []
        self.injuries_total = injuries_total
        self.injuries_fatal = injuries_fatal
        self.injuries_incapacitating = injuries_incapacitating
        self.injuries_non_incapacitating = injuries_non_incapacitating
        self.injuries_reported_not_evident = injuries_reported_not_evident
        self.injuries_no_indication = injuries_no_indication
        self.crash_hour = crash_hour
        self.crash_day_of_week = crash_day_of_week
        self.crash_month = crash_month

    def set_crash_date_from_timestamp(self, crash_date: str):
        try:
            self.data = datetime.datetime.strptime(crash_date[:10], self.DATE_FORMAT).date()
            self.crash_date = crash_date
            self.crash_day_of_week = self.data.isoweekday()
            self.crash_month = self.data.month
        except ValueError:
            print(f"Invalid date format: {crash_date}")

    def get_intersection_related_str(self) -> str:
        return "S" if self.intersection_related_i else "N"
    
    def set_intersection_related_from_str(self, value: str):
        self.intersection_related_i = value.strip().upper() == "S"

    @staticmethod
    def list_to_string(lst: List[str]) -> str:
        return " , ".join(lst)

    def to_byte_array(self) -> bytes:
        try:
            ba = bytearray()
            # Pack fixed-size values
            ba += struct.pack('>i', self.ID_registro)
            ba += self._pack_string(self.crash_date)
            
            # Convert date to epoch days
            epoch = datetime.date(1970, 1, 1)
            days = (self.data - epoch).days
            ba += struct.pack('>q', days)
            
            # Pack strings
            for attr in [
                self.traffic_control_device,
                self.weather_condition,
                self.list_to_string(self.lighting_condition),
                self.first_crash_type,
                self.trafficway_type,
                self.alignment,
                self.roadway_surface_cond,
                self.road_defect,
                self.list_to_string(self.crash_type),
                self.get_intersection_related_str(),
                self.damage,
                self.prim_contributory_cause
            ]:
                ba += self._pack_string(attr)
            
            # Pack integers and floats
            ba += struct.pack('>i', self.num_units)
            ba += self._pack_string(self.list_to_string(self.most_severe_injury))
            ba += struct.pack('>f', self.injuries_total)
            ba += struct.pack('>f', self.injuries_fatal)
            ba += struct.pack('>f', self.injuries_incapacitating)
            ba += struct.pack('>f', self.injuries_non_incapacitating)
            ba += struct.pack('>f', self.injuries_reported_not_evident)
            ba += struct.pack('>f', self.injuries_no_indication)
            ba += struct.pack('>i', self.crash_hour)
            ba += struct.pack('>i', self.crash_day_of_week)
            ba += struct.pack('>i', self.crash_month)
            
            return bytes(ba)
        except Exception as e:
            print(f"Serialization error: {e}")
            return b''

    @classmethod
    def from_byte_array(cls, data: bytes):
        try:
            obj = cls()
            offset = 0
            
            # Unpack fixed-size values
            obj.ID_registro = struct.unpack_from('>i', data, offset)[0]
            offset += 4
            obj.crash_date, offset = cls._unpack_string(data, offset)
            
            # Unpack date (epoch days)
            days = struct.unpack_from('>q', data, offset)[0]
            offset += 8
            obj.data = datetime.date(1970, 1, 1) + datetime.timedelta(days=days)
            
            # Unpack strings
            string_attrs = [
                'traffic_control_device',
                'weather_condition',
                'lighting_condition',
                'first_crash_type',
                'trafficway_type',
                'alignment',
                'roadway_surface_cond',
                'road_defect',
                'crash_type',
                'intersection_related_i',
                'damage',
                'prim_contributory_cause'
            ]
            
            for attr in string_attrs:
                value, offset = cls._unpack_string(data, offset)
                if attr == 'lighting_condition':
                    obj.lighting_condition = [s.strip() for s in value.split(',')] if value else []
                elif attr == 'crash_type':
                    obj.crash_type = [s.strip() for s in value.split(',')] if value else []
                elif attr == 'intersection_related_i':
                    obj.set_intersection_related_from_str(value)
                else:
                    setattr(obj, attr, value)
            
            # Unpack integers and floats
            obj.num_units = struct.unpack_from('>i', data, offset)[0]
            offset += 4
            
            severe_injury_str, offset = cls._unpack_string(data, offset)
            obj.most_severe_injury = [s.strip() for s in severe_injury_str.split(',')] if severe_injury_str else []
            
            float_attrs = [
                'injuries_total',
                'injuries_fatal',
                'injuries_incapacitating',
                'injuries_non_incapacitating',
                'injuries_reported_not_evident',
                'injuries_no_indication'
            ]
            
            for attr in float_attrs:
                setattr(obj, attr, struct.unpack_from('>f', data, offset)[0])
                offset += 4
                
            int_attrs = [
                'crash_hour',
                'crash_day_of_week',
                'crash_month'
            ]
            
            for attr in int_attrs:
                setattr(obj, attr, struct.unpack_from('>i', data, offset)[0])
                offset += 4
            
            return obj
        except Exception as e:
            print(f"Deserialization error: {e}")
            return None

    @staticmethod
    def _pack_string(s: str) -> bytes:
        """Pack string with 2-byte length prefix (big-endian)"""
        if s is None:
            s = ""
        encoded = s.encode('utf-8')
        return struct.pack('>H', len(encoded)) + encoded

    @staticmethod
    def _unpack_string(data: bytes, offset: int) -> Tuple[str, int]:
        """Unpack string with 2-byte length prefix (big-endian)"""
        length = struct.unpack_from('>H', data, offset)[0]
        offset += 2
        s = data[offset:offset+length].decode('utf-8')
        return s, offset + length

    def __str__(self):
        return (
            f"ID Registro: {self.ID_registro}\n"
            f"Data do Acidente: {self.crash_date}\n"
            f"Data (LocalDate): {self.data.strftime(self.DATE_FORMAT)}\n"
            f"Dispositivo de controle de tráfego: {self.traffic_control_device}\n"
            f"Condição climática: {self.weather_condition}\n"
            f"Condição de iluminação: {self.list_to_string(self.lighting_condition)}\n"
            f"Tipo de primeira colisão: {self.first_crash_type}\n"
            f"Tipo de via de tráfego: {self.trafficway_type}\n"
            f"Alinhamento: {self.alignment}\n"
            f"Condição da superfície da via: {self.roadway_surface_cond}\n"
            f"Defeito na estrada: {self.road_defect}\n"
            f"Tipo de acidente: {self.list_to_string(self.crash_type)}\n"
            f"Interseção relacionada: {self.get_intersection_related_str()}\n"
            f"Danos: {self.damage}\n"
            f"Causa contributiva primária: {self.prim_contributory_cause}\n"
            f"Número de unidades: {self.num_units}\n"
            f"Ferimento mais grave: {self.list_to_string(self.most_severe_injury)}\n"
            f"Total de ferimentos: {self.injuries_total:.1f}\n"
            f"Ferimentos fatais: {self.injuries_fatal:.1f}\n"
            f"Lesões incapacitantes: {self.injuries_incapacitating:.1f}\n"
            f"Lesões não incapacitantes: {self.injuries_non_incapacitating:.1f}\n"
            f"Lesões relatadas não evidentes: {self.injuries_reported_not_evident:.1f}\n"
            f"Lesões sem indicação: {self.injuries_no_indication:.1f}\n"
            f"Hora do acidente: {self.crash_hour}\n"
            f"Dia da semana: {self.crash_day_of_week}\n"
            f"Mês: {self.crash_month}"
        )


# ==============================================
# File Handling
# ==============================================
class FileHandler:
    @staticmethod
    def read_csv(path: str) -> List[DataObject]:
        """Read CSV file and return list of DataObjects"""
        objects = []
        try:
            with open(path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file, delimiter=';')
                next(reader)  # Skip header
                for row in reader:
                    if len(row) < 22:  # Adjusted for actual columns
                        print(f"Skipping invalid row: {row}")
                        continue
                    
                    obj = DataObject()
                    obj.set_crash_date_from_timestamp(
                        f"{row[0][3:5]}/{row[0][0:2]}/{row[0][6:10]} {row[0][11:]}"
                    )
                    obj.traffic_control_device = row[1]
                    obj.weather_condition = row[2]
                    obj.lighting_condition = [s.strip() for s in row[3].split(',')] if row[3] else []
                    obj.first_crash_type = row[4]
                    obj.trafficway_type = row[5]
                    obj.alignment = row[6]
                    obj.roadway_surface_cond = row[7]
                    obj.road_defect = row[8]
                    obj.crash_type = [s.strip() for s in row[9].split('/')] if row[9] else []
                    obj.set_intersection_related_from_str(row[10])
                    obj.damage = row[11]
                    obj.prim_contributory_cause = row[12]
                    obj.num_units = int(row[13]) if row[13] else 0
                    obj.most_severe_injury = [s.strip() for s in row[14].split(',')] if row[14] else []
                    
                    # Handle float conversion safely
                    float_fields = [
                        row[15], row[16], row[17], row[18], row[19], row[20]]
                    float_values = [0.0] * 6
                    
                    for i, val in enumerate(float_fields):
                        try:
                            float_values[i] = float(val) if val else 0.0
                        except ValueError:
                            pass
                    
                    (obj.injuries_total, obj.injuries_fatal, obj.injuries_incapacitating,
                     obj.injuries_non_incapacitating, obj.injuries_reported_not_evident,
                     obj.injuries_no_indication) = float_values
                    
                    obj.crash_hour = int(row[21]) if row[21] else 0
                    objects.append(obj)
            
            print(f"Successfully read {len(objects)} records from CSV")
            return objects
        except Exception as e:
            print(f"Error reading CSV: {e}")
            return []

    @staticmethod
    def write_db(objects: List[DataObject], path: str):
        """Write objects to database file"""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb') as file:
                # Write header with last ID
                last_id = objects[-1].ID_registro if objects else 0
                file.write(struct.pack('>i', last_id))
                
                # Write records
                for obj in objects:
                    data = obj.to_byte_array()
                    file.write(struct.pack('>i', obj.ID_registro))
                    file.write(struct.pack('?', True))  # Active record
                    file.write(struct.pack('>i', len(data)))
                    file.write(data)
            print(f"Successfully wrote {len(objects)} records to database")
        except Exception as e:
            print(f"Error writing database: {e}")

    @staticmethod
    def read_db(path: str) -> List[DataObject]:
        """Read database file and return list of DataObjects"""
        objects = []
        try:
            if not os.path.exists(path):
                print(f"Database file not found: {path}")
                return []
                
            with open(path, 'rb') as file:
                # Read header
                last_id = struct.unpack('>i', file.read(4))[0]
                
                while file.tell() < os.path.getsize(path):
                    record_id = struct.unpack('>i', file.read(4))[0]
                    active = struct.unpack('?', file.read(1))[0]
                    size = struct.unpack('>i', file.read(4))[0]
                    data = file.read(size)
                    
                    if active:
                        obj = DataObject.from_byte_array(data)
                        if obj:
                            objects.append(obj)
            print(f"Successfully read {len(objects)} records from database")
            return objects
        except Exception as e:
            print(f"Error reading database: {e}")
            return []

    @staticmethod
    def update_record(path: str, record_id: int, updated_obj: DataObject):
        """Update a record in the database"""
        try:
            # Read all records
            records = []
            with open(path, 'rb') as file:
                last_id = struct.unpack('>i', file.read(4))[0]
                
                while file.tell() < os.path.getsize(path):
                    pos = file.tell()
                    rid = struct.unpack('>i', file.read(4))[0]
                    active = struct.unpack('?', file.read(1))[0]
                    size = struct.unpack('>i', file.read(4))[0]
                    data = file.read(size)
                    
                    if rid == record_id and active:
                        # Mark existing record as inactive
                        records.append((pos, rid, False, size, data))
                        # Add updated record at end
                        new_data = updated_obj.to_byte_array()
                        records.append((None, rid, True, len(new_data), new_data))
                    else:
                        records.append((pos, rid, active, size, data))
            
            # Write all records back
            with open(path, 'wb') as file:
                file.write(struct.pack('>i', last_id))
                for pos, rid, active, size, data in records:
                    if pos is None:  # New record
                        file.write(struct.pack('>i', rid))
                        file.write(struct.pack('?', active))
                        file.write(struct.pack('>i', size))
                        file.write(data)
                    else:  # Existing record
                        file.write(struct.pack('>i', rid))
                        file.write(struct.pack('?', active))
                        file.write(struct.pack('>i', size))
                        file.write(data)
            print(f"Record {record_id} updated successfully")
            return True
        except Exception as e:
            print(f"Error updating record: {e}")
            return False

    @staticmethod
    def delete_record(path: str, record_id: int):
        """Mark a record as deleted in the database"""
        try:
            with open(path, 'r+b') as file:
                file.read(4)  # Skip header
                
                while file.tell() < os.path.getsize(path):
                    pos = file.tell()
                    rid = struct.unpack('>i', file.read(4))[0]
                    active = struct.unpack('?', file.read(1))[0]
                    size = struct.unpack('>i', file.read(4))[0]
                    
                    if rid == record_id and active:
                        # Mark record as inactive
                        file.seek(pos + 4)
                        file.write(struct.pack('?', False))
                        print(f"Record {record_id} marked as deleted")
                        return True
                    
                    # Move to next record
                    file.seek(pos + 4 + 1 + 4 + size)
            print(f"Record {record_id} not found")
            return False
        except Exception as e:
            print(f"Error deleting record: {e}")
            return False


# ==============================================
# Indexed File Handling
# ==============================================
class IndexedFileHandler:
    INDEX_ENTRY_SIZE = 13  # 4 (ID) + 8 (pointer) + 1 (active flag)
    
    @staticmethod
    def write_from_csv(csv_path: str, data_file_path: str, index_file_path: str):
        """Import data from CSV to indexed database"""
        try:
            # Create necessary directories
            os.makedirs(os.path.dirname(data_file_path), exist_ok=True)
            os.makedirs(os.path.dirname(index_file_path), exist_ok=True)
            
            with open(data_file_path, 'wb') as data_file, \
                 open(index_file_path, 'wb') as index_file:
                
                # Write initial header (last ID = 0)
                index_file.write(struct.pack('>i', 0))
                last_id = 0
                
                with open(csv_path, 'r', encoding='utf-8') as csv_file:
                    reader = csv.reader(csv_file, delimiter=';')
                    next(reader)  # Skip header
                    
                    for row in reader:
                        if len(row) < 22:  # Adjusted for actual columns
                            continue
                        
                        # Create DataObject from CSV row
                        obj = DataObject()
                        obj.set_crash_date_from_timestamp(
                            f"{row[0][3:5]}/{row[0][0:2]}/{row[0][6:10]} {row[0][11:]}"
                        )
                        obj.traffic_control_device = row[1]
                        obj.weather_condition = row[2]
                        obj.lighting_condition = [s.strip() for s in row[3].split(',')] if row[3] else []
                        obj.first_crash_type = row[4]
                        obj.trafficway_type = row[5]
                        obj.alignment = row[6]
                        obj.roadway_surface_cond = row[7]
                        obj.road_defect = row[8]
                        obj.crash_type = [s.strip() for s in row[9].split('/')] if row[9] else []
                        obj.set_intersection_related_from_str(row[10])
                        obj.damage = row[11]
                        obj.prim_contributory_cause = row[12]
                        obj.num_units = int(row[13]) if row[13] else 0
                        obj.most_severe_injury = [s.strip() for s in row[14].split(',')] if row[14] else []
                        
                        # Handle float conversion safely
                        float_fields = [
                            row[15], row[16], row[17], row[18], row[19], row[20]]
                        float_values = [0.0] * 6
                        
                        for i, val in enumerate(float_fields):
                            try:
                                float_values[i] = float(val) if val else 0.0
                            except ValueError:
                                pass
                        
                        (obj.injuries_total, obj.injuries_fatal, obj.injuries_incapacitating,
                         obj.injuries_non_incapacitating, obj.injuries_reported_not_evident,
                         obj.injuries_no_indication) = float_values
                        
                        obj.crash_hour = int(row[21]) if row[21] else 0
                        
                        # Assign ID and increment
                        last_id += 1
                        obj.ID_registro = last_id
                        
                        # Write to data file
                        data_pos = data_file.tell()
                        data = obj.to_byte_array()
                        data_file.write(struct.pack('?', True))  # Active flag
                        data_file.write(struct.pack('>i', len(data)))
                        data_file.write(data)
                        
                        # Write to index file
                        index_file.write(struct.pack('>i', obj.ID_registro))
                        index_file.write(struct.pack('>q', data_pos))
                        index_file.write(struct.pack('?', True))
                
                # Update header with last ID
                index_file.seek(0)
                index_file.write(struct.pack('>i', last_id))
            
            print(f"Successfully imported {last_id} records to indexed database")
            return True
        except Exception as e:
            print(f"Error importing CSV to indexed database: {e}")
            return False

    @staticmethod
    def find_index_entry(index_file_path: str, record_id: int) -> Tuple[Union[int, None], Union[bool, None]]:
        """Find index entry using binary search"""
        try:
            if not os.path.exists(index_file_path):
                return None, None
                
            with open(index_file_path, 'rb') as index_file:
                # Read header (last ID)
                last_id = struct.unpack('>i', index_file.read(4))[0]
                
                # Binary search in sorted index
                low, high = 0, last_id - 1
                while low <= high:
                    mid = (low + high) // 2
                    # Calculate position of index entry
                    index_file.seek(4 + mid * IndexedFileHandler.INDEX_ENTRY_SIZE)
                    
                    # Read index entry
                    entry_id = struct.unpack('>i', index_file.read(4))[0]
                    pointer = struct.unpack('>q', index_file.read(8))[0]
                    active = struct.unpack('?', index_file.read(1))[0]
                    
                    if entry_id == record_id:
                        return pointer, active
                    elif entry_id < record_id:
                        low = mid + 1
                    else:
                        high = mid - 1
            return None, None
        except Exception as e:
            print(f"Error finding index entry: {e}")
            return None, None

    @staticmethod
    def read_record(data_file_path: str, index_file_path: str, record_id: int) -> Union[DataObject, None]:
        """Read record using index"""
        pointer, active = IndexedFileHandler.find_index_entry(index_file_path, record_id)
        if pointer is None or not active:
            return None
            
        try:
            with open(data_file_path, 'rb') as data_file:
                data_file.seek(pointer)
                active = struct.unpack('?', data_file.read(1))[0]
                if not active:
                    return None
                    
                size = struct.unpack('>i', data_file.read(4))[0]
                data = data_file.read(size)
                return DataObject.from_byte_array(data)
        except Exception as e:
            print(f"Error reading record from data file: {e}")
            return None

    @staticmethod
    def update_record(data_file_path: str, index_file_path: str, 
                      record_id: int, updated_obj: DataObject) -> bool:
        """Update a record in the indexed database"""
        pointer, active = IndexedFileHandler.find_index_entry(index_file_path, record_id)
        if pointer is None or not active:
            return False
            
        new_data = updated_obj.to_byte_array()
        
        try:
            with open(data_file_path, 'r+b') as data_file:
                # Check if new data fits in existing space
                data_file.seek(pointer)
                old_active = struct.unpack('?', data_file.read(1))[0]
                old_size = struct.unpack('>i', data_file.read(4))[0]
                
                if len(new_data) <= old_size:
                    # Overwrite existing record
                    data_file.seek(pointer)
                    data_file.write(struct.pack('?', True))
                    data_file.write(struct.pack('>i', len(new_data)))
                    data_file.write(new_data)
                else:
                    # Write new record at end of file
                    data_file.seek(0, os.SEEK_END)
                    new_pointer = data_file.tell()
                    data_file.write(struct.pack('?', True))
                    data_file.write(struct.pack('>i', len(new_data)))
                    data_file.write(new_data)
                    
                    # Update index entry
                    with open(index_file_path, 'r+b') as index_file:
                        # Find index entry position
                        last_id = struct.unpack('>i', index_file.read(4))[0]
                        low, high = 0, last_id - 1
                        while low <= high:
                            mid = (low + high) // 2
                            pos = 4 + mid * IndexedFileHandler.INDEX_ENTRY_SIZE
                            index_file.seek(pos)
                            entry_id = struct.unpack('>i', index_file.read(4))[0]
                            
                            if entry_id == record_id:
                                # Update pointer
                                index_file.seek(pos + 4)
                                index_file.write(struct.pack('>q', new_pointer))
                                break
                            elif entry_id < record_id:
                                low = mid + 1
                            else:
                                high = mid - 1
                
                    # Mark old record as deleted
                    data_file.seek(pointer)
                    data_file.write(struct.pack('?', False))
            return True
        except Exception as e:
            print(f"Error updating record: {e}")
            return False

    @staticmethod
    def delete_record(data_file_path: str, index_file_path: str, record_id: int) -> bool:
        """Mark a record as deleted in the indexed database"""
        pointer, active = IndexedFileHandler.find_index_entry(index_file_path, record_id)
        if pointer is None or not active:
            return False
            
        try:
            # Update index entry
            with open(index_file_path, 'r+b') as index_file:
                last_id = struct.unpack('>i', index_file.read(4))[0]
                low, high = 0, last_id - 1
                while low <= high:
                    mid = (low + high) // 2
                    pos = 4 + mid * IndexedFileHandler.INDEX_ENTRY_SIZE
                    index_file.seek(pos)
                    entry_id = struct.unpack('>i', index_file.read(4))[0]
                    
                    if entry_id == record_id:
                        # Mark as deleted
                        index_file.seek(pos + 12)
                        index_file.write(struct.pack('?', False))
                        break
                    elif entry_id < record_id:
                        low = mid + 1
                    else:
                        high = mid - 1
            
            # Update data file
            with open(data_file_path, 'r+b') as data_file:
                data_file.seek(pointer)
                data_file.write(struct.pack('?', False))
            
            return True
        except Exception as e:
            print(f"Error deleting record: {e}")
            return False


# ==============================================
# Compression Algorithms
# ==============================================
class CompressionHandler:
    @staticmethod
    def _build_huffman_tree(freq):
        heap = [[weight, [byte, ""]] for byte, weight in freq.items()]
        heapq.heapify(heap)
        while len(heap) > 1:
            lo = heapq.heappop(heap)
            hi = heapq.heappop(heap)
            for pair in lo[1:]:
                pair[1] = '0' + pair[1]
            for pair in hi[1:]:
                pair[1] = '1' + pair[1]
            heapq.heappush(heap, [lo[0] + hi[0]] + lo[1:] + hi[1:])
        return heap[0]

    @staticmethod
    def huffman_compress(input_file: str, output_file: str):
        """Huffman compression (character-based)"""
        start_time = time.time()
        
        try:
            # Read input data
            with open(input_file, 'r', encoding='utf-8') as f:
                data = f.read()
            
            # Build frequency table
            freq = defaultdict(int)
            for char in data:
                freq[char] += 1
            
            # Build Huffman tree and generate codes
            huff_tree = CompressionHandler._build_huffman_tree(freq)
            huff_codes = dict(huff_tree[1:])
            
            # Encode data
            encoded_data = ''.join(huff_codes[char] for char in data)
            
            # Pad encoded data to make it multiple of 8
            extra_padding = 8 - len(encoded_data) % 8
            encoded_data += '0' * extra_padding
            
            # Convert bit string to bytes
            byte_array = bytearray()
            for i in range(0, len(encoded_data), 8):
                byte = encoded_data[i:i+8]
                byte_array.append(int(byte, 2))
            
            # Write to file
            with open(output_file, 'wb') as f:
                # Write metadata
                f.write(struct.pack('I', len(data)))  # Original data length
                f.write(struct.pack('I', extra_padding))  # Padding length
                f.write(struct.pack('I', len(freq)))  # Frequency table size
                
                # Write frequency table
                for char, count in freq.items():
                    f.write(char.encode('utf-8'))
                    f.write(struct.pack('I', count))
                
                # Write compressed data
                f.write(bytes(byte_array))
            
            # Calculate stats
            original_size = os.path.getsize(input_file)
            compressed_size = os.path.getsize(output_file)
            ratio = (compressed_size / original_size) * 100
            elapsed = time.time() - start_time
            
            print(f"Compression complete: {input_file} -> {output_file}")
            print(f"Original size: {original_size} bytes")
            print(f"Compressed size: {compressed_size} bytes")
            print(f"Compression ratio: {ratio:.2f}%")
            print(f"Time: {elapsed:.2f} seconds")
            return True
        except Exception as e:
            print(f"Compression error: {e}")
            return False

    @staticmethod
    def huffman_decompress(input_file: str, output_file: str):
        """Huffman decompression (character-based)"""
        start_time = time.time()
        
        try:
            with open(input_file, 'rb') as f:
                # Read metadata
                data_len = struct.unpack('I', f.read(4))[0]
                padding = struct.unpack('I', f.read(4))[0]
                freq_size = struct.unpack('I', f.read(4))[0]
                
                # Rebuild frequency table
                freq = {}
                for _ in range(freq_size):
                    char = f.read(1).decode('utf-8')
                    count = struct.unpack('I', f.read(4))[0]
                    freq[char] = count
                
                # Read compressed data
                compressed_data = f.read()
            
            # Rebuild Huffman tree and generate reverse codes
            huff_tree = CompressionHandler._build_huffman_tree(freq)
            reverse_codes = {code: char for char, code in dict(huff_tree[1:]).items()}
            
            # Convert bytes to bit string
            bit_string = ""
            for byte in compressed_data:
                bits = bin(byte)[2:].rjust(8, '0')
                bit_string += bits
            
            # Remove padding
            bit_string = bit_string[:-padding] if padding > 0 else bit_string
            
            # Decode data
            current_code = ""
            decoded_data = []
            
            for bit in bit_string:
                current_code += bit
                if current_code in reverse_codes:
                    decoded_data.append(reverse_codes[current_code])
                    current_code = ""
            
            # Write decompressed data
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(''.join(decoded_data))
            
            # Verify
            original_size = os.path.getsize(input_file)
            decompressed_size = os.path.getsize(output_file)
            elapsed = time.time() - start_time
            
            print(f"Decompression complete: {input_file} -> {output_file}")
            print(f"Compressed size: {original_size} bytes")
            print(f"Decompressed size: {decompressed_size} bytes")
            print(f"Time: {elapsed:.2f} seconds")
            return True
        except Exception as e:
            print(f"Decompression error: {e}")
            return False

    @staticmethod
    def huffman_byte_compress(input_file: str, output_file: str):
        """Huffman compression (byte-based)"""
        start_time = time.time()
        
        try:
            # Read input data
            with open(input_file, 'rb') as f:
                data = f.read()
            
            # Build frequency table
            freq = defaultdict(int)
            for byte in data:
                freq[byte] += 1
            
            # Build Huffman tree and generate codes
            huff_tree = CompressionHandler._build_huffman_tree(freq)
            huff_codes = dict(huff_tree[1:])
            
            # Encode data
            bit_string = ''.join(huff_codes[byte] for byte in data)
            
            # Pad encoded data to make it multiple of 8
            padding = 8 - len(bit_string) % 8
            bit_string += '0' * padding
            
            # Convert bit string to bytes
            byte_array = bytearray()
            for i in range(0, len(bit_string), 8):
                byte = bit_string[i:i+8]
                byte_array.append(int(byte, 2))
            
            # Write to file
            with open(output_file, 'wb') as f:
                # Write metadata
                f.write(struct.pack('I', len(data)))  # Original data length
                f.write(struct.pack('I', padding))  # Padding length
                f.write(struct.pack('I', len(freq)))  # Frequency table size
                
                # Write frequency table
                for byte, count in freq.items():
                    f.write(struct.pack('B', byte))
                    f.write(struct.pack('I', count))
                
                # Write compressed data
                f.write(bytes(byte_array))
            
            # Calculate stats
            original_size = os.path.getsize(input_file)
            compressed_size = os.path.getsize(output_file)
            ratio = (compressed_size / original_size) * 100
            elapsed = time.time() - start_time
            
            print(f"Compression complete: {input_file} -> {output_file}")
            print(f"Original size: {original_size} bytes")
            print(f"Compressed size: {compressed_size} bytes")
            print(f"Compression ratio: {ratio:.2f}%")
            print(f"Time: {elapsed:.2f} seconds")
            return True
        except Exception as e:
            print(f"Compression error: {e}")
            return False

    @staticmethod
    def huffman_byte_decompress(input_file: str, output_file: str):
        """Huffman decompression (byte-based)"""
        start_time = time.time()
        
        try:
            with open(input_file, 'rb') as f:
                # Read metadata
                data_len = struct.unpack('I', f.read(4))[0]
                padding = struct.unpack('I', f.read(4))[0]
                freq_size = struct.unpack('I', f.read(4))[0]
                
                # Rebuild frequency table
                freq = {}
                for _ in range(freq_size):
                    byte = struct.unpack('B', f.read(1))[0]
                    count = struct.unpack('I', f.read(4))[0]
                    freq[byte] = count
                
                # Read compressed data
                compressed_data = f.read()
            
            # Rebuild Huffman tree and generate reverse codes
            huff_tree = CompressionHandler._build_huffman_tree(freq)
            reverse_codes = {code: byte for byte, code in dict(huff_tree[1:]).items()}
            
            # Convert bytes to bit string
            bit_string = ""
            for byte in compressed_data:
                bits = bin(byte)[2:].rjust(8, '0')
                bit_string += bits
            
            # Remove padding
            bit_string = bit_string[:-padding] if padding > 0 else bit_string
            
            # Decode data
            current_code = ""
            decoded_data = bytearray()
            
            for bit in bit_string:
                current_code += bit
                if current_code in reverse_codes:
                    decoded_data.append(reverse_codes[current_code])
                    current_code = ""
            
            # Write decompressed data
            with open(output_file, 'wb') as f:
                f.write(decoded_data)
            
            # Verify
            original_size = os.path.getsize(input_file)
            decompressed_size = os.path.getsize(output_file)
            elapsed = time.time() - start_time
            
            print(f"Decompression complete: {input_file} -> {output_file}")
            print(f"Compressed size: {original_size} bytes")
            print(f"Decompressed size: {decompressed_size} bytes")
            print(f"Time: {elapsed:.2f} seconds")
            return True
        except Exception as e:
            print(f"Decompression error: {e}")
            return False

    @staticmethod
    def lzw_compress(input_file: str, output_file: str):
        """LZW compression"""
        start_time = time.time()
        
        try:
            # Initialize dictionary
            dict_size = 256
            dictionary = {bytes([i]): i for i in range(dict_size)}
            
            # Read input data
            with open(input_file, 'rb') as f:
                data = f.read()
            
            # Compression
            w = bytes()
            compressed = []
            
            for byte in data:
                wc = w + bytes([byte])
                if wc in dictionary:
                    w = wc
                else:
                    compressed.append(dictionary[w])
                    # Add new sequence to dictionary
                    if dict_size < 65536:  # Limit to 16-bit codes
                        dictionary[wc] = dict_size
                        dict_size += 1
                    w = bytes([byte])
            
            if w:
                compressed.append(dictionary[w])
            
            # Write to file
            with open(output_file, 'wb') as f:
                # Write number of codes
                f.write(struct.pack('I', len(compressed)))
                # Write codes
                for code in compressed:
                    f.write(struct.pack('H', code))  # Use 2-byte unsigned int
            
            # Calculate stats
            original_size = os.path.getsize(input_file)
            compressed_size = os.path.getsize(output_file)
            ratio = (compressed_size / original_size) * 100
            elapsed = time.time() - start_time
            
            print(f"Compression complete: {input_file} -> {output_file}")
            print(f"Original size: {original_size} bytes")
            print(f"Compressed size: {compressed_size} bytes")
            print(f"Compression ratio: {ratio:.2f}%")
            print(f"Time: {elapsed:.2f} seconds")
            return True
        except Exception as e:
            print(f"Compression error: {e}")
            return False

    @staticmethod
    def lzw_decompress(input_file: str, output_file: str):
        """LZW decompression"""
        start_time = time.time()
        
        try:
            # Initialize dictionary
            dict_size = 256
            dictionary = {i: bytes([i]) for i in range(dict_size)}
            
            # Read compressed data
            with open(input_file, 'rb') as f:
                num_codes = struct.unpack('I', f.read(4))[0]
                codes = [struct.unpack('H', f.read(2))[0] for _ in range(num_codes)]
            
            # Decompression
            result = bytearray()
            w = dictionary[codes[0]]
            result.extend(w)
            
            for k in codes[1:]:
                if k in dictionary:
                    entry = dictionary[k]
                elif k == dict_size:
                    entry = w + bytes([w[0]])
                else:
                    raise ValueError(f"Bad compressed code: {k}")
                
                result.extend(entry)
                
                # Add new sequence to dictionary
                if dict_size < 65536:  # Limit to 16-bit codes
                    dictionary[dict_size] = w + bytes([entry[0]])
                    dict_size += 1
                
                w = entry
            
            # Write decompressed data
            with open(output_file, 'wb') as f:
                f.write(result)
            
            # Verify
            original_size = os.path.getsize(input_file)
            decompressed_size = os.path.getsize(output_file)
            elapsed = time.time() - start_time
            
            print(f"Decompression complete: {input_file} -> {output_file}")
            print(f"Compressed size: {original_size} bytes")
            print(f"Decompressed size: {decompressed_size} bytes")
            print(f"Time: {elapsed:.2f} seconds")
            return True
        except Exception as e:
            print(f"Decompression error: {e}")
            return False


# ==============================================
# Cryptography Handler
# ==============================================
class CryptographyHandler:
    @staticmethod
    def blowfish_encrypt_file():
        input_file = input("Caminho do arquivo de entrada: ").strip()
        output_file = input("Caminho do arquivo de saída: ").strip()
        password = getpass.getpass("Senha: ")
        
        if not os.path.exists(input_file):
            print("Arquivo de entrada não encontrado!")
            return False
        
        try:
            encrypt_file(input_file, output_file, password)
            print("Criptografia Blowfish concluída com sucesso!")
            return True
        except Exception as e:
            print(f"Erro na criptografia: {e}")
            return False

    @staticmethod
    def blowfish_decrypt_file():
        input_file = input("Caminho do arquivo criptografado: ").strip()
        output_file = input("Caminho do arquivo descriptografado: ").strip()
        password = getpass.getpass("Senha: ")
        
        if not os.path.exists(input_file):
            print("Arquivo de entrada não encontrado!")
            return False
        
        try:
            decrypt_file(input_file, output_file, password)
            print("Descriptografia Blowfish concluída com sucesso!")
            return True
        except Exception as e:
            print(f"Erro na descriptografia: {e}")
            return False

    @staticmethod
    def generate_rsa_keys():
        key_dir = "crypto_keys"
        os.makedirs(key_dir, exist_ok=True)
        
        key = RSA.generate(2048)
        private_key = key.export_key()
        public_key = key.publickey().export_key()
        
        with open(os.path.join(key_dir, "private.pem"), "wb") as f:
            f.write(private_key)
        
        with open(os.path.join(key_dir, "public.pem"), "wb") as f:
            f.write(public_key)
        
        print(f"Chaves RSA geradas e salvas em {key_dir}/")
        return True

    @staticmethod
    def hybrid_encrypt_file():
        input_file = input("Caminho do arquivo de entrada: ").strip()
        output_file = input("Caminho do arquivo de saída: ").strip()
        public_key_file = input("Caminho da chave pública RSA: ").strip()
        
        if not os.path.exists(input_file):
            print("Arquivo de entrada não encontrado!")
            return False
        if not os.path.exists(public_key_file):
            print("Arquivo de chave pública não encontrado!")
            return False
        
        try:
            # Generate random AES key
            aes_key = get_random_bytes(32)  # 256-bit key
            
            # Encrypt file with AES
            iv = get_random_bytes(16)
            cipher_aes = AES.new(aes_key, AES.MODE_CBC, iv)
            
            with open(input_file, 'rb') as f:
                plaintext = f.read()
            
            padded_data = pad(plaintext, AES.block_size)
            ciphertext = cipher_aes.encrypt(padded_data)
            
            # Encrypt AES key with RSA
            with open(public_key_file, 'rb') as f:
                public_key = RSA.import_key(f.read())
            
            rsa_cipher = PKCS1_OAEP.new(public_key)
            enc_aes_key = rsa_cipher.encrypt(aes_key)
            
            # Write output file
            with open(output_file, 'wb') as f:
                f.write(struct.pack('>I', len(enc_aes_key)))
                f.write(enc_aes_key)
                f.write(iv)
                f.write(ciphertext)
            
            print("Criptografia híbrida concluída com sucesso!")
            return True
        except Exception as e:
            print(f"Erro na criptografia híbrida: {e}")
            return False

    @staticmethod
    def hybrid_decrypt_file():
        input_file = input("Caminho do arquivo criptografado: ").strip()
        output_file = input("Caminho do arquivo descriptografado: ").strip()
        private_key_file = input("Caminho da chave privada RSA: ").strip()
        
        if not os.path.exists(input_file):
            print("Arquivo de entrada não encontrado!")
            return False
        if not os.path.exists(private_key_file):
            print("Arquivo de chave privada não encontrado!")
            return False
        
        try:
            with open(input_file, 'rb') as f:
                # Read encrypted AES key
                key_len = struct.unpack('>I', f.read(4))[0]
                enc_aes_key = f.read(key_len)
                iv = f.read(16)
                ciphertext = f.read()
            
            # Decrypt AES key with RSA
            with open(private_key_file, 'rb') as f:
                private_key = RSA.import_key(f.read())
            
            rsa_cipher = PKCS1_OAEP.new(private_key)
            aes_key = rsa_cipher.decrypt(enc_aes_key)
            
            # Decrypt file with AES
            cipher_aes = AES.new(aes_key, AES.MODE_CBC, iv)
            decrypted_data = unpad(cipher_aes.decrypt(ciphertext), AES.block_size)
            
            with open(output_file, 'wb') as f:
                f.write(decrypted_data)
            
            print("Descriptografia híbrida concluída com sucesso!")
            return True
        except Exception as e:
            print(f"Erro na descriptografia híbrida: {e}")
            return False


# ==============================================
# Menu System
# ==============================================
class MenuSystem:
    @staticmethod
    def main_menu():
        """Display the main menu and handle user input"""
        while True:
            print("\n" + "="*50)
            print("Sistema de Gerenciamento de Acidentes de Trânsito")
            print("="*50)
            print("1. Parte I - Gerenciamento de Dados")
            print("2. Parte II - Indexação e Busca")
            print("3. Parte III - Compactação de Dados")
            print("4. Parte IV - Criptografia")
            print("5. Sair")
            print("="*50)
            
            choice = input("Selecione uma opção: ").strip()
            
            if choice == "1":
                MenuSystem.part1_menu()
            elif choice == "2":
                MenuSystem.part2_menu()
            elif choice == "3":
                MenuSystem.part3_menu()
            elif choice == "4":
                MenuSystem.part4_menu()
            elif choice == "5":
                print("Saindo do sistema...")
                return
            else:
                print("Opção inválida. Tente novamente.")

    @staticmethod
    def part1_menu():
        """Display Part 1 menu and handle user input"""
        db_path = "data/traffic_accidents.db"
        while True:
            print("\n" + "="*50)
            print("Parte I - Gerenciamento de Dados")
            print("="*50)
            print("1. Importar dados de CSV")
            print("2. Listar todos os registros")
            print("3. Buscar registro por ID")
            print("4. Atualizar registro")
            print("5. Excluir registro")
            print("6. Voltar ao menu principal")
            print("="*50)
            
            choice = input("Selecione uma opção: ").strip()
            
            if choice == "1":
                csv_path = input("Caminho do arquivo CSV: ").strip()
                if not os.path.exists(csv_path):
                    print("Arquivo não encontrado!")
                    continue
                    
                objects = FileHandler.read_csv(csv_path)
                for i, obj in enumerate(objects):
                    obj.ID_registro = i + 1
                FileHandler.write_db(objects, db_path)
            elif choice == "2":
                objects = FileHandler.read_db(db_path)
                if not objects:
                    print("Nenhum registro encontrado!")
                    continue
                    
                for obj in objects:
                    print("\n" + "="*50)
                    print(obj)
            elif choice == "3":
                try:
                    record_id = int(input("ID do registro: ").strip())
                    objects = FileHandler.read_db(db_path)
                    found = [obj for obj in objects if obj.ID_registro == record_id]
                    if found:
                        print("\n" + "="*50)
                        print(found[0])
                    else:
                        print("Registro não encontrado")
                except ValueError:
                    print("ID inválido")
            elif choice == "4":
                try:
                    record_id = int(input("ID do registro para atualizar: ").strip())
                    objects = FileHandler.read_db(db_path)
                    found = [obj for obj in objects if obj.ID_registro == record_id]
                    
                    if found:
                        updated_obj = MenuSystem.update_object_ui(found[0])
                        if FileHandler.update_record(db_path, record_id, updated_obj):
                            print("Registro atualizado com sucesso!")
                    else:
                        print("Registro não encontrado")
                except ValueError:
                    print("ID inválido")
            elif choice == "5":
                try:
                    record_id = int(input("ID do registro para excluir: ").strip())
                    if FileHandler.delete_record(db_path, record_id):
                        print("Registro excluído com sucesso!")
                except ValueError:
                    print("ID inválido")
            elif choice == "6":
                return
            else:
                print("Opção inválida. Tente novamente.")

    @staticmethod
    def part2_menu():
        """Display Part 2 menu and handle user input"""
        data_path = "indexed_data/traffic_accidents.db"
        index_path = "indexed_data/indexTrafficAccidents.db"
        os.makedirs("indexed_data", exist_ok=True)
        
        while True:
            print("\n" + "="*50)
            print("Parte II - Indexação e Busca")
            print("="*50)
            print("1. Importar dados de CSV (indexado)")
            print("2. Buscar registro por ID (indexado)")
            print("3. Atualizar registro (indexado)")
            print("4. Excluir registro (indexado)")
            print("5. Voltar ao menu principal")
            print("="*50)
            
            choice = input("Selecione uma opção: ").strip()
            
            if choice == "1":
                csv_path = input("Caminho do arquivo CSV: ").strip()
                if not os.path.exists(csv_path):
                    print("Arquivo não encontrado!")
                    continue
                    
                if IndexedFileHandler.write_from_csv(csv_path, data_path, index_path):
                    print("Dados importados com sucesso!")
            elif choice == "2":
                try:
                    record_id = int(input("ID do registro: ").strip())
                    obj = IndexedFileHandler.read_record(data_path, index_path, record_id)
                    if obj:
                        print("\n" + "="*50)
                        print(obj)
                    else:
                        print("Registro não encontrado ou excluído")
                except ValueError:
                    print("ID inválido")
            elif choice == "3":
                try:
                    record_id = int(input("ID do registro para atualizar: ").strip())
                    obj = IndexedFileHandler.read_record(data_path, index_path, record_id)
                    if obj:
                        updated_obj = MenuSystem.update_object_ui(obj)
                        if IndexedFileHandler.update_record(data_path, index_path, record_id, updated_obj):
                            print("Registro atualizado com sucesso!")
                    else:
                        print("Registro não encontrado")
                except ValueError:
                    print("ID inválido")
            elif choice == "4":
                try:
                    record_id = int(input("ID do registro para excluir: ").strip())
                    if IndexedFileHandler.delete_record(data_path, index_path, record_id):
                        print("Registro excluído com sucesso!")
                except ValueError:
                    print("ID inválido")
            elif choice == "5":
                return
            else:
                print("Opção inválida. Tente novamente.")

    @staticmethod
    def part3_menu():
        """Display Part 3 menu and handle user input"""
        while True:
            print("\n" + "="*50)
            print("Parte III - Compactação de Dados")
            print("="*50)
            print("1. Compactar arquivo (Huffman)")
            print("2. Descompactar arquivo (Huffman)")
            print("3. Compactar arquivo (Huffman Byte)")
            print("4. Descompactar arquivo (Huffman Byte)")
            print("5. Compactar arquivo (LZW)")
            print("6. Descompactar arquivo (LZW)")
            print("7. Voltar ao menu principal")
            print("="*50)
            
            choice = input("Selecione uma opção: ").strip()
            
            if choice == "1":
                input_file = input("Caminho do arquivo de entrada: ").strip()
                output_file = input("Caminho do arquivo de saída (.huffc): ").strip()
                if not os.path.exists(input_file):
                    print("Arquivo de entrada não encontrado!")
                    continue
                CompressionHandler.huffman_compress(input_file, output_file)
            elif choice == "2":
                input_file = input("Caminho do arquivo compactado (.huffc): ").strip()
                output_file = input("Caminho do arquivo descompactado: ").strip()
                if not os.path.exists(input_file):
                    print("Arquivo compactado não encontrado!")
                    continue
                CompressionHandler.huffman_decompress(input_file, output_file)
            elif choice == "3":
                input_file = input("Caminho do arquivo de entrada: ").strip()
                output_file = input("Caminho do arquivo de saída (.huffb): ").strip()
                if not os.path.exists(input_file):
                    print("Arquivo de entrada não encontrado!")
                    continue
                CompressionHandler.huffman_byte_compress(input_file, output_file)
            elif choice == "4":
                input_file = input("Caminho do arquivo compactado (.huffb): ").strip()
                output_file = input("Caminho do arquivo descompactado: ").strip()
                if not os.path.exists(input_file):
                    print("Arquivo compactado não encontrado!")
                    continue
                CompressionHandler.huffman_byte_decompress(input_file, output_file)
            elif choice == "5":
                input_file = input("Caminho do arquivo de entrada: ").strip()
                output_file = input("Caminho do arquivo de saída (.lzw): ").strip()
                if not os.path.exists(input_file):
                    print("Arquivo de entrada não encontrado!")
                    continue
                CompressionHandler.lzw_compress(input_file, output_file)
            elif choice == "6":
                input_file = input("Caminho do arquivo compactado (.lzw): ").strip()
                output_file = input("Caminho do arquivo descompactado: ").strip()
                if not os.path.exists(input_file):
                    print("Arquivo compactado não encontrado!")
                    continue
                CompressionHandler.lzw_decompress(input_file, output_file)
            elif choice == "7":
                return
            else:
                print("Opção inválida. Tente novamente.")

    @staticmethod
    def part4_menu():
        """Display Part 4 menu for cryptography operations"""
        while True:
            print("\n" + "="*50)
            print("Parte IV - Criptografia")
            print("="*50)
            print("1. Criptografar arquivo (Blowfish)")
            print("2. Descriptografar arquivo (Blowfish)")
            print("3. Gerar chaves RSA")
            print("4. Criptografia Híbrida (AES + RSA) - Criptografar")
            print("5. Criptografia Híbrida (AES + RSA) - Descriptografar")
            print("6. Voltar ao menu principal")
            print("="*50)
            
            choice = input("Selecione uma opção: ").strip()
            
            if choice == "1":
                CryptographyHandler.blowfish_encrypt_file()
            elif choice == "2":
                CryptographyHandler.blowfish_decrypt_file()
            elif choice == "3":
                CryptographyHandler.generate_rsa_keys()
            elif choice == "4":
                CryptographyHandler.hybrid_encrypt_file()
            elif choice == "5":
                CryptographyHandler.hybrid_decrypt_file()
            elif choice == "6":
                return
            else:
                print("Opção inválida. Tente novamente.")

    @staticmethod
    def update_object_ui(obj: DataObject) -> DataObject:
        """Update a DataObject through user input"""
        print("\nAtualize os campos (deixe em branco para manter o valor atual)")
        print("="*50)
        
        # Date and time
        new_date = input(f"Data do Acidente [{obj.crash_date}]: ").strip()
        if new_date:
            obj.set_crash_date_from_timestamp(new_date)
        
        # String fields
        fields = [
            ("Dispositivo de controle de tráfego", "traffic_control_device"),
            ("Condição climática", "weather_condition"),
            ("Tipo de primeira colisão", "first_crash_type"),
            ("Tipo de via de tráfego", "trafficway_type"),
            ("Alinhamento", "alignment"),
            ("Condição da superfície da via", "roadway_surface_cond"),
            ("Defeito na estrada", "road_defect"),
            ("Danos", "damage"),
            ("Causa contributiva primária", "prim_contributory_cause")
        ]
        
        for label, attr in fields:
            current_val = getattr(obj, attr)
            new_val = input(f"{label} [{current_val}]: ").strip()
            if new_val:
                setattr(obj, attr, new_val)
        
        # List fields
        list_fields = [
            ("Condições de iluminação (separadas por vírgula)", "lighting_condition"),
            ("Tipos de acidente (separados por vírgula)", "crash_type"),
            ("Ferimentos mais graves (separados por vírgula)", "most_severe_injury")
        ]
        
        for label, attr in list_fields:
            current = ", ".join(getattr(obj, attr))
            new_val = input(f"{label} [{current}]: ").strip()
            if new_val:
                setattr(obj, attr, [s.strip() for s in new_val.split(",")])
        
        # Boolean field
        intersection = input(f"Interseção relacionada (S/N) [{obj.get_intersection_related_str()}]: ").strip()
        if intersection:
            obj.set_intersection_related_from_str(intersection)
        
        # Numeric fields
        numeric_fields = [
            ("Número de unidades", "num_units", int),
            ("Total de ferimentos", "injuries_total", float),
            ("Ferimentos fatais", "injuries_fatal", float),
            ("Lesões incapacitantes", "injuries_incapacitating", float),
            ("Lesões não incapacitantes", "injuries_non_incapacitating", float),
            ("Lesões relatadas não evidentes", "injuries_reported_not_evident", float),
            ("Lesões sem indicação", "injuries_no_indication", float),
            ("Hora do acidente", "crash_hour", int)
        ]
        
        for label, attr, conv_type in numeric_fields:
            current_val = getattr(obj, attr)
            while True:
                new_val = input(f"{label} [{current_val}]: ").strip()
                if not new_val:
                    break
                try:
                    setattr(obj, attr, conv_type(new_val))
                    break
                except ValueError:
                    print(f"Valor inválido. Digite um {'número inteiro' if conv_type == int else 'número'}.")
        
        print("\nRegistro atualizado:")
        print("="*50)
        print(obj)
        return obj


# ==============================================
# Main Execution
# ==============================================
if __name__ == "__main__":
    # Create necessary directories
    os.makedirs("data", exist_ok=True)
    os.makedirs("indexed_data", exist_ok=True)
    os.makedirs("crypto_keys", exist_ok=True)
    
    # Start the menu system
    MenuSystem.main_menu()