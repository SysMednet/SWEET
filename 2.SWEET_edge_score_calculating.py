import argparse
import numpy as np
import sys


def check_file(expres):
    checkset = set(["", "NA", "Na", "na", "nan", "null"])
    for c in checkset:
        loc = np.where(expres == c)
        if loc[0].size:
            expres[loc] = "0"
            print(f"{c} in expres and transfer to 0")
    return expres


parser = argparse.ArgumentParser(description="Manual")
parser.add_argument("-f", type=str, default="./example/expression.txt",
                    help="A path to 'gene expression matrix' file")  # gene expression matrix
parser.add_argument("-w", type=str, default="./example/weight.txt",
                    help="A path to 'sample weight' file (i.e., the output file from step 1)")  # sample weight file
parser.add_argument("-p", type=str, default="./example/patient.txt",
                    help="A path to 'samples of interest' file")  # samples of interest
parser.add_argument("-g", type=str, default="./example/gene.txt",
                    help="A path to 'genes of interest' file")  # genes of interest
parser.add_argument("-s", type=str, default="./example",
                    help="A path to the output 'confidence scores of edges' files for each sample of interest")  # output path

args = parser.parse_args()
file_e, file_w = args.f, args.w
file_p, file_g = args.p, args.g
save_path = (args.s).rstrip('/')

# open patient file
patset = set()
with open(file_p, mode='r') as rline:
    for nline in rline:
        tem = nline.strip('\n').split('\t')
        patset.add(tem[0])
del rline, nline, tem
if not patset:
    print("patient file doesn't have patients")
    sys.exit()

# open gene file
geneset = set()
with open(file_g, mode='r') as rline:
    for nline in rline:
        tem = nline.strip('\n').split('\t')
        geneset.add(tem[0])
del rline, nline, tem
if not geneset:
    print("gene file doesn't have genes")
    sys.exit()

# open weight file
weight = {}
with open(file_w, mode='r') as rline:
    _ = rline.readline()
    for nline in rline:
        p, w, *_ = nline.strip('\n').split('\t')
        weight.update({p: float(w)})
del rline, nline, p, w, _
if not weight:
    print("weight file doesn't have pateint")
    sys.exit()

# open expression file
gene, value = [], []
with open(file_e, mode='r') as rline:
    pat = rline.readline().strip('\n').split('\t')[1:]
    for nline in rline:
        g, *v = nline.strip('\n').split('\t')
        if g in geneset:
            value += v
            gene.append(g)
del rline, nline, g, v
patlen, genelen = len(pat), len(gene)
if (not patlen):
    print("expression file are empty")
    sys.exit()

# check the pateints and genes in expression file
patloc = [l for l, p in enumerate(pat) if p in patset]
if (not genelen) or (len(patloc) != len(patset)):
    print("expression file doesn't map to pateint or gene file")
    sys.exit()
if len(set(pat) & weight.keys()) != patlen:
    print("expression file doesn't map to weight file")
    sys.exit()
del patset, geneset
print(f"patient : {len(patloc)}\ngene : {genelen}")

gene = np.array(gene)
value = np.array(value).reshape(genelen, patlen)
value = check_file(value)
value = value.astype(float)
loc = np.where(np.sum(value, axis=1) == 0)
if len(loc[0]) != 0:
    tem = ','.join(str(i)for i in gene[loc])
    print('Delete gene with 0 expression in all patients: '+tem)
    value = np.delete(value, loc, 0)
    gene = np.delete(gene, loc)

# value = np.array(value,dtype=float)


agg = np.corrcoef(value)

for l in patloc:
    p = pat[l]
    value_s = np.c_[value, value[:, l]]
    value_s = np.corrcoef(value_s)
    value_s = weight[p] * (value_s - agg) + agg
    with open(f"{save_path}/{p}.txt", mode='w') as wline:
        wline.write("gene1\tgene2\tRaw_edge_score\n")
        for l, g1, v1 in zip(range(genelen), gene, value_s):
            wline.write('\n'.join(g1+'\t'+g2+'\t'+str(v2)
                        for g2, v2 in zip(gene[(l+1):], v1[(l+1):])))
            wline.write('\n')

del value, agg, patloc, value_s, p, wline, weight, l, g1, v1

print("Finish")