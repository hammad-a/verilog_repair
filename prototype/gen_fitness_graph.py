import sys
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import statistics

fname = sys.argv[1]
popsize = -1

log_file = open(fname, "r")
lines = log_file.readlines()
log_file.close()

f_values = []

it = iter(lines)

raw_data = {}
gen = -1

while(True):
    line = next(it, None)
    if line == None:
        break
    if line.startswith("TOTAL TIME"):
        break
    
    line = line.strip()

    if "--template_seeding-->" in line:
        pass
    elif line.startswith("IN GENERATION"):
        gen = int(line.split(" ")[2])
        raw_data[gen] = []
    elif "-->" in line:
        fval = line.split("\t\t")[1]
        if " " in fval: # crossover
            fvals = fval.split(" ")
            for tmp in fvals:
                raw_data[gen].append(float(tmp))
        else: # mutation
            raw_data[gen].append(float(fval))

means = []
mins = []
maxes = []
medians = []
gens = list(raw_data.keys())

for i in gens:
    fvals = raw_data[i]
    # print("Generation %d" % i)
    # print("Mean = %f" % statistics.mean(fvals))
    # print("Median = %f" % statistics.median(fvals))
    # print("Max = %f" % max(fvals))
    # print("Min %f" % min(fvals))
    # print()
    means.append(statistics.mean(fvals))
    mins.append(min(fvals))
    maxes.append(max(fvals))
    medians.append(statistics.median(fvals))

# print(gens)
# print(means)
# print(mins)
# print(maxes)
# print(medians)
plt.ylabel('Normalized Fitness')
plt.xlabel('Generation #')
plt.xticks(range(0,len(gens)))
plt.title('Mean Fitness')
plt.plot(gens, means, 'r') 
plt.show()
plt.clf()

plt.ylabel('Normalized Fitness')
plt.xlabel('Generation #')
plt.xticks(range(0,len(gens)))
plt.title('Max Fitness')
plt.plot(gens, maxes, 'r') 
plt.show()
plt.clf()

plt.ylabel('Normalized Fitness')
plt.xlabel('Generation #')
plt.xticks(range(0,len(gens)))
plt.title('Min Fitness')
plt.plot(gens, mins, 'r') 
plt.show()
plt.clf()


