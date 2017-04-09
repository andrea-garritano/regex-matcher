# Semplice Matcher di espressioni regolari

Realizzato per il corso di Theoretical Computer Science in collaborazione con il professor Andrew D. Bagdanov


This is a very simple recursive descent parser that parses a simple regular expression dialect into an object hierarchy (the parse tree of the regular expression).

This is the basic CFG that is parsed:

**S -> A | C | K**
 
**K -> S***
 
**A -> (S+S)**
 
**C -> (SS)**
 
**L -> a | b | c | d | ... | LL**

This grammar is *mostly* correct, but there are some shortcuts that
are supported in how expressions are parsed. The biggest one is that
the LAST character in a multi-character literal concatenation can be
STARRED. This is just to support expressions like: ab*, ababc*, etc.

Note also that the grammar is extremely picky about expressions
being fully-parenthesized. 

Some examples:

**NOT VALID:**

 (a+b)*a*     (the concatenation is not parenthesized)
 
 (a+b+c)      (one alternation is not parenthesized)
 
 (a+b)+c      (one alternation still not parenthesized)
 
**VALID:**

 ((a+b)*a*)
 
 ((a+b)+c)
