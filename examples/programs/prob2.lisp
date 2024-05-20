

(defvar a 1)
(defvar b 1)
(defvar next)
(defvar sum 0)

(loop_while (< b 4000000)
    (setq next (+ a b))
    (if (= 0 (mod b 2))
        (setq sum (+ sum b))
        0
    )
    (setq a b)
    (setq b next)
)
(print_int sum)

