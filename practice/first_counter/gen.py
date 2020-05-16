tokenfile = "./tokens_temp.txt"
with open(tokenfile) as f:
    lines = f.readlines()
    for line in lines:
        if line not in ['\n', '\r\n']:
            token = line.split(' ')[0]
            print token
