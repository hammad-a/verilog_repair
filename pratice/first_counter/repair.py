import sys
#i, j: replace jth with ith

def replace(l, i, t):
    l[i] = t

def delete(l, i):
    l[i] = ""

token_file = sys.argv[1]
i = int(sys.argv[2])
j = int(sys.argv[3])

with open(token_file) as f:
    src_tokens = f.readlines()
    outf = open("./candidates/candidate_"+str(i)+"_"+str(j)+".v","w")
    main_token = src_tokens[i]
    replace(src_tokens, j, main_token)
    for m in range(len(src_tokens)):
        outf.write(src_tokens[m])
    outf.close()





