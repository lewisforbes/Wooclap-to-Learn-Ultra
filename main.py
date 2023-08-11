from re import findall
from os import listdir, rename, remove
import csv

class Main:
    def __init__(self):
        self.wooclap_delim  = ','  # input delim
        self.learn_delim    = '\t' # output delim
        
        self.in_dir     = "input/"
        self.to_convert = listdir(self.in_dir)
        self.out_dir    = "output/"

        self.blank = '' #blank cell
        self.reset_output()
        self.convert()
        
        self.current_file = None
        input("Finished.\nPress enter to exit.")

    ### MAIN ###
    def convert(self):
        for fname in self.to_convert:
            converted = []
            not_converted = []
            first = True
            self.current_file = fname
            for line in self.read_csv(self.in_dir+fname):
                if first:
                    first = False
                    continue

                conv_f = self.qtype_to_converter(line[0])
                if conv_f == None:
                    not_converted.append(line)
                else:
                    conv_attempt = conv_f(line)
                    if conv_attempt == None:
                        not_converted.append(line)
                    else:
                        converted.append(conv_attempt)

            self.write_csv(self.one_line_title(converted),       self.out_dir+"{} {}".format("[converted]", fname),      delim=self.learn_delim)
            self.write_csv(not_converted,   self.out_dir+"{} {}".format("[not converted]", fname),  delim=self.wooclap_delim)

    ### INPUT/OUTPUT ### 
    def reset_output(self):
        for fname in listdir(self.out_dir):
            remove(self.out_dir+fname)

    def read_csv(self, fpath):
        f = open(fpath, "r")
        output = []
        for line in csv.reader(f, quotechar='"', delimiter=self.wooclap_delim, quoting=csv.QUOTE_ALL, skipinitialspace=True):
            output.append(line)
        return output
    
    def write_csv(self, lines, fpath, delim):
        if len(lines)==0:
            return

        with open(fpath, 'w', newline='') as file:
            mywriter = csv.writer(file, delimiter=delim)
            mywriter.writerows(lines)
        
        rename(fpath, fpath.replace(".csv", ".txt"))


    ### QUESTION CONVERTERS ### 
    def convert_MCQ(self, line):
        if len(line)<4:
            return self.error("Line too short.", line)
        
        qtype = self.qtype_name_converter(line[0])
        title = line[1]
        correct = line[2].split(",")
        try:
            correct = [int(a.strip())-1 for a in correct] # correct now indexing from 0
            1/len(correct) # wtf
        except:
            return self.error("correct answer formatted incorrectly", line)

        output = [qtype, title]
        cor_str = "correct"
        incor_str = "incorrect"
        for i, ans in enumerate(line[3:]):
            if ans==self.blank:
                break
            output.append(ans)
            if i in correct:
                output.append(cor_str)
            else:
                output.append(incor_str)
        
        return output
    
    def convert_Poll(self, line):
        if len(line)<4:
            return self.error("line too short", line)
        
        qtype = self.qtype_name_converter(line[0])
        title = line[1]
        options = line[3:]
        output = [qtype, title]
        for opt in options:
            if opt==self.blank:
                break
            output += [opt, "correct"]

        return output
    
    def convert_OpenQuestion(self, line):
        if len(line)<2:
            return self.error("line too short", line)
        
        qtype = self.qtype_name_converter(line[0])
        title = line[1]
        placeholder = "Enter your response here."
        return [qtype, title, placeholder] 

    def convert_GuessNumber(self, line):
        if len(line)<3:
            return self.error("Line too short.", line)
        
        qtype = self.qtype_name_converter(line[0])
        title = line[1]
        try:
            correct = float(line[2])
        except:
            return self.error("numeric answer in wrong format", line)
        
        return [qtype, title, str(correct)]

    def convert_Matching(self, line):
        if len(line)<4:
            return self.error("line too short", line)
        qtype = self.qtype_name_converter(line[0])
        title = line[1]
        output = [qtype, title]
        
        for pair in line[3:]:
            if pair == self.blank:
                break
            pair_split = [s.strip() for s in pair.split("---")]
            if len(pair_split)!=2:
                return self.error("Incorrectly formatted pair: " + str(pair_split), line)
            output += pair_split

        return output

    def convert_FillInTheBlanks(self, line):
        if len(line)<4:
            return self.error("line too short", line)
        
        qtype = self.qtype_name_converter(line[0])
        title = line[1]

        qtext = line[3]
        sols = findall(r"\[(.*?)\]", qtext)
        if len(sols)>10:
            return self.error("too many blanks - max is 10", line)

        varnames = "abcdefghij"
        vars = {}        
        for i, s in enumerate(sols):
            qtext = qtext.replace("[{}]".format(s), "[{}]".format(varnames[i]))
            vars[varnames[i]] = s

        output = [qtype, title+": "+qtext]
        for var, value in vars.items():
            output += [var, value, None]

        return output


    ### LOOKUPS ### 
    def qtype_to_converter(self, qtype):
        qtypes = {"MCQ":                self.convert_MCQ,
                  "Poll":               self.convert_Poll,
                  "Rating":             None,
                  "OpenQuestion":       self.convert_OpenQuestion,
                  "GuessNumber":        self.convert_GuessNumber,
                  "Matching":           self.convert_Matching,
                  "Prioritization":     None,
                  "Sorting":            None,
                  "FillInTheBlanks":    self.convert_FillInTheBlanks,
                  "Brainstorm":         None,
                  "Concordance":        None,
                  "SCTJudgment":        None}
        if not qtype in qtypes.keys():
            return self.error("invalid qtype provided", qtype)
        return qtypes[qtype]
        
    def qtype_name_converter(self, wc_name):
        qtypes = {"MCQ":               "MA",
                  "Poll":               "MA",
                  "Rating":             None,
                  "OpenQuestion":       "ESS",
                  "GuessNumber":        "NUM",
                  "Matching":           "MAT",
                  "Prioritization":     None,
                  "Sorting":            None,
                  "FillInTheBlanks":    "FIB_PLUS",
                  "Brainstorm":         None,
                  "Concordance":        None,
                  "SCTJudgment":        None}
        if not wc_name in qtypes.keys():
            return self.error("Invalid qtype provided.", wc_name)
        return qtypes[wc_name]
    
    ### OTHER ###
    def one_line_title(self, lines, title_i=1):
        output = []
        for l in lines:
            l[title_i] = l[title_i].split("\n")[-1]
            output.append(l)
        return output

    def error(self, msg, line):
        print("Unable to convert line in file '{}' ({}):\n{}\n".format(self.current_file, msg, str(line)))
        return None

m = Main()
# print(m.convert_MCQ(["MCQ", "example title", "", "ans a", "ans b"]))
# print(m.convert_Matching(["Matching", "example title", "", "A1 --- A2", "B1 --- B2"]))
# print(m.convert_FillInTheBlanks(["FillInTheBlanks", "example title", "", "roses are [red], violets are [blue], one thing i wanna say to all is huge [uwu]"]))