  ORG   0000H
  AJMP  MAIN
  ORG   50H

MAIN:
  INC   A
  MOV   A, #7FH

; loop
LOOP:
  MOV   P1, A
  RR    A
  ACALL DELAY
  JMP   LOOP

DELAY:
  MOV   R5, #255
D1:
  DJNZ  R5, D1
  RET ; return to loop
