# Example on Python
#
# def print_rhombus(n):
#     a = n-1
#     b = n-1
#     while a > 0:
#         pos = 0
#         while pos < b+1:
#             if pos == b:
#                 print("#")
#             elif pos == a:
#                 print("#", end="")
#             else:
#                 print(" ", end="")
#             pos += 1
#         b += 1
#         a -= 1
#     while a < b+1:
#         pos = 0
#         while pos < b+1:
#             if pos == b:
#                 print("#")
#             elif pos == a:
#                 print("#", end="")
#             else:
#                 print(" ", end="")
#             pos += 1
#         a += 1
#         b -= 1
#
# print_rhombus(2)

# Same program on lisp


# Функция, которая печатает РОМБ со стороной длины n из символов sym

(defun print_rhombus(n sym)
    (defvar a (- n 1))
    (defvar b a)
    (defvar pos)
    (loop_while (> a 0)
        (setq pos 0)
        (loop_while (< pos (+ b 1))
            (if (= pos b)
                (and
                    (print_str sym)
                    (print_char 10)     # newline
                )
                #else
                (if (= pos a)
                    (print_str sym)
                    #else
                    (print_char 32)     # space
                )
            )
            (setq pos (+ pos 1))
        )
        (setq a (- a 1))
        (setq b (+ b 1))
    )
    (loop_while (< a (+ b 1))
        (setq pos 0)
        (loop_while (< pos (+ b 1))
            (if (= pos b)
                (and
                    (print_str sym)
                    (print_char 10)     # newline
                )
                #else
                (if (= pos a)
                    (print_str sym)
                    #else
                    (print_char 32)     # space
                )
            )
            (setq pos (+ pos 1))
        )
        (setq a (+ a 1))
        (setq b (- b 1))
    )
)

(print_rhombus 5 "8")   # Напечатать РОМБ со стороной длинны 5 из символов "8"
