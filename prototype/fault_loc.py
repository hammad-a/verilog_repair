f = open("oracle.txt", "r")
oracle = f.readlines()
f.close()

f = open("output.txt", "r")
sim = f.readlines()
f.close()

diff_bits = []

def strip_bits(bits):
    for i in range(len(bits)):
        bits[i] = bits[i].strip()
    return bits

if len(oracle) != len(sim):
    print("Exiting")
    sys.exit(1)

headers = oracle[0].split(",")

for i in range(1, len(oracle)):
    clk = oracle[i].split(",")[0]
    tmp_oracle = strip_bits(oracle[i].split(",")[1:])
    tmp_sim = strip_bits(sim[i].split(",")[1:])
    
    for b in range(len(tmp_oracle)):
        if tmp_oracle[b] != tmp_sim[b]:
            diff_bits.append(headers[b])

res = set()

for i in range(len(diff_bits)):
    tmp = diff_bits[i]
    if "[" in tmp:      
        res.add(tmp.split("[")[0])
    else:
        res.add(tmp)

print(res)
