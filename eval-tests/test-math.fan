<start> ::= <expr>
<expr> ::= <term> <expr_tail>
<expr_tail> ::= "" | "+" <term> <expr_tail> | "-" <term> <expr_tail>
<term> ::= <factor> <term_tail>
<term_tail> ::= "" | "*" <factor> <term_tail> | "/" <nonzero_number> <term_tail>
<factor> ::= <number> | "(" <expr> ")"
<number> ::= "0" | <nonzero_digit> <digits>
<nonzero_number> ::= <nonzero_digit> <digits>
<digits> ::= "" | <digit> <digits>
<digit> ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"
<nonzero_digit> ::= "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"

# 1. abs of the evaluation -42 is less or equal 10
where abs(eval(str(<start>)) - 42) <= 25

# 2. Tutti i numeri generati devono essere pari
where forall <n> in <number>: int(str(<n>)) % 2 == 0
where forall <n> in <nonzero_number>: int(str(<n>)) % 2 == 0

# 3. lunghezza minima dell'espressione
where 10 <= len(str(<start>)) <= 40
