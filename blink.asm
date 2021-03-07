  ORG   0000H
  AJMP  MAIN
  ORG   0050H

MAIN:
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
