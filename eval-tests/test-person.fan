<start> ::= <person_record>
<person_record> ::= <name> "," <age>
<name> ::= <first_name> " " <last_name>
<first_name> ::= <word>
<last_name> ::= <word>
<word> ::= <uppercase> <lowercase>+
<uppercase> ::= "A" | "B" | "C" | "D" | "E" | "F" | "G" | "H" | "I" | "J" | "K" | "L" | "M" | "N" | "O" | "P" | "Q" | "R" | "S" | "T" | "U" | "V" | "W" | "X" | "Y" | "Z"
<lowercase> ::= "a" | "b" | "c" | "d" | "e" | "f" | "g" | "h" | "i" | "j" | "k" | "l" | "m" | "n" | "o" | "p" | "q" | "r" | "s" | "t" | "u" | "v" | "w" | "x" | "y" | "z"
<age> ::= <digit>+
<digit> ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"

# 1. Tutti i nomi iniziano con 'A'
where forall <w> in <word>: str(<w>).startswith("A")

# 2. Età compresa tra 21 e 100
where 21 <= int(str(<age>)) and int(str(<age>)) <= 100

# 3. Età divisibile per 7
where int(str(<age>)) % 7 == 0

# 4. Lunghezza di ogni nome tra 8 e 12
where forall <w> in <word>: 8 <= len(str(<w>)) <= 20
