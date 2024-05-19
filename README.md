# Лабораторная №3. Эксперимент.

- Клиодт Вадим Дмитриевич, P3234
- Вариант: `lisp -> asm | stack | harv | hw | instr | struct | stream | port | cstr | prob2 | cache`
- Базовый вариант

## Язык программирования
### Синтаксис
Форма Бэкуса-Наура:
```BNF
<program> ::= {<expression_list>}

<expression_list> ::= <expression> | <expression> <expression_list>

<expression> ::= <defvar>
               | <setq>
               | <defun>
               | <loop_while>
               | <if>
               | <print_str>
               | <print_int>
               | <read_str>
               | <arithmetic_expr>
               | <comparison_expr>
               | <logical_expr>
               | <function_call>
               | <identifier>
               | <number>
               | <string>

<defvar> ::= "(defvar" <identifier> [<expression>] ")"

<setq> ::= "(setq" <identifier> <expression> ")"

<defun> ::= "(defun" <identifier> "(" <param_list> ")" <expression_list> ")"

<param_list> ::= <identifier> | <identifier> <param_list>

<loop_while> ::= "(loop_while" <expression> [<expression_list>] ")"

<if> ::= "(if" <expression> <expression> <expression> ")"

<print_str> ::= "(print_str" /<expression>/ ")"

<print_int> ::= "(print_int" <expression> ")"

<read_str> ::= "(read_str)"

<arithmetic_expr> ::= "(+" {<expression>} ")"
                    | "(-" /<expression>/ ")"
                    | "(*" {<expression>} ")"
                    | "(/" /<expression>/ ")"
                    | "(mod" <expression> <expression> ")"

<comparison_expr> ::= "(=" <expression> [<expression>] ")"
                    | "(>" <expression> [<expression>] ")"
                    | "(<" <expression> [<expression>] ")"

<logical_expr> ::= "(and" /<expression>/ ")"
                 | "(or" /<expression>/ ")"
                 | "(not" <expression> ")"

<function_call> ::= "(" <identifier> <expression_list> ")"

<identifier> ::= <letter> { <letter> | <digit> | "_" }

<string> ::= "\"" { <any_character_except_double_quote> } "\""

<number> ::= ["-"] <digit> { <digit> }

<letter> ::= "a" | "b" | ... | "z" | "A" | "B" | ... | "Z"

<digit> ::= "0" | "1" | "2" | ... | "9"

```

### Семантика
Комментарии:
- Начинаются со знака `#` и идут до конца строки.

Операции:
- `defvar` - объявление переменной и присваивание ей переданного значения или 0, если значения не передано. Все переменные имеют глобальную область видимости. Объявление переменной обязательно до других операций с ней. Возвращает значение переменной.
- `setq` - присвоить переменной значение. Возвращает значение переменной.
- `loop_while` - выполняет код в цикле, пока истинно условие. `(loop_while (A) (B) (C) (D) ...)` - означает `while (A) {B; C; D; ... }`. Возвращает ноль.
- `if` - условный оператор.  `(if (A) (B) (C))` - означает `if (A) {B} else {C}`. Возвращает значение выполненного выражения.
- `print_str` - выводит строку. Возвращает адрес последнего напечатанного символа.
- `print_int` - выводит число. Возвращает ноль.
- `read_str` - читает строку. Возвращает указатель на ее начало.
- `+` `-` `*` `/` `mod` - арифметические операции (сложение, вычитание, умножение, целочисленное деление, взятие остатка). Возвращают свой результат.
-  `=` `>` `<` - операторы сравнения. Возвращают 1 или 0 (true/false соотв.)
- `and` `or` `not` - булевы операторы. and возвращает первое ложное, иначе, если такого нет, последнее. or возвращает первое истинное, иначе, если такого нет, последнее. not возвращает 1 или 0 (true/false соотв.)
- `defun` - объявление функции. Разрешен только на верхнем уровне вложенности. Выполняется только при вызове. Возвращает то, что вернуло последнее выражение в теле функции. Пример объявления и вызова: 
```lisp
(defun print_sum(a b) (print_int (+ a b)))
(print_sum 123 987)
```
Возможна **рекурсия**: 
```lisp
(defun decrement_and_print(a)       # объявление функции и переменной а
    (if (< 0 a)                     # проверка условия
        (and                        # and используется для выполнения нескольких выражений в блоке
            (setq a (- a 1))        # декрементировать а
            (print_int a)           # напечатать а
            (print_str " ")         # напечатать пробел
            (decrement_and_print a) # рекурсивный вызов
        )
    0)                              # пустой блок else
)

(decrement_and_print 5)             # вызов функции

# Выводит: 4 3 2 1 0
```

Порядок выполнения: 
- Все операции выполняются последовательно. Сначала последовательно выполняются внутренние выражения, потом внешние. Наприер, для `(A (B) (C))` порядок будет B-C-A.

Литералы:
- Целые числовые. Возвращают себя.
- Строковые, пишутся в двойных кавычках, длина не ограничена. Возвращают указатель на место в памяти, где записаны.

Память: 
- Выделяется статически на этапе трансляции
- Строковые литералы помещаются в память в начале работы программы
- Динамически считываемые строки ограничены длинной 40 символов

Видимость переменных и функций:
- Глобальная после их объявления

# Организация памяти
Модель памяти:
- Гарвардская архитектура - раздельная память команд и данных
- Размер машинного слова не определён
- Размер памяти данных задается при начале симуляции 
- Имеет линейное адресное пространство
- В памяти данных хранятся статические строки и переменных
- В памяти команд хранятся инструкции для выполнения
- Взаимодействие с памятью данных происходит при помощи инструкций `LOAD` и `STORE`. LOAD - загружает в вершину стека данные по адресу с вершины стека. STORE - сохраняет данные в память из второй ячейки стека по адресу с вершины стека.

Стеки:
- Имеются стек данных и стек возвратов (в соответствии со стековой моделью процессора)
- Оба поддерживают операции `push` и `pop`
- Стек данных поддерживает операции `dup` и `swap`, а также чтение из второй от вершины ячейки (предполагается реализация на уровне схемотехники)

Регистры:
- PC - счетчик команд
- AR - регистр адреса

# Система команд
## Набор инструкций

| Команда                                                         | Число тактов | Стек ДО                                                                           | Стек ПОСЛЕ                                                                         | Описание                                                                                                                                                                                       |
|:----------------------------------------------------------------|--------------|:----------------------------------------------------------------------------------|------------------------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| PUSH [value]                                                    | 1            | <table><tr><td>...</td></tr><tr><td>...</td></tr><tr><td>...</td></tr></table>    | <table><tr><td>...</td></tr><tr><td>...</td></tr><tr><td>value</td></tr></table>   | пушит на вершину стека свой аргумент                                                                                                                                                           |
| LOAD                                                            | 2            | <table><tr><td>...</td></tr><tr><td>...</td></tr><tr><td>addr</td></tr></table>   | <table><tr><td>...</td></tr><tr><td>...</td></tr><tr><td>value</td></tr></table>   | загружает значение из памяти, адрес берется из вершины стека                                                                                                                                   |
| STORE                                                           | 2            | <table><tr><td>...</td></tr><tr><td>value</td></tr><tr><td>addr</td></tr></table> | <table><tr><td>...</td></tr><tr><td>...</td></tr><tr><td>value</td></tr></table>   | сохраняет значение из второй ячейки стека, адрес берется из вершины стека                                                                                                                      |
| POP                                                             | 1            | <table><tr><td>...</td></tr><tr><td>...</td></tr><tr><td>value</td></tr></table>  | <table><tr><td>...</td></tr><tr><td>...</td></tr><tr><td>...</td></tr></table>     | удаляет вершину стека                                                                                                                                                                          |
| ADD<br/>SUB<br/>MUL<br/>DIV<br/>MOD                             | 1            | <table><tr><td>...</td></tr><tr><td>a</td></tr><tr><td>b</td></tr></table>        | <table><tr><td>...</td></tr><tr><td>...</td></tr><tr><td>result</td></tr></table>  | выполняет арифметическую операцию                                                                                                                                                              |
| FLAGS                                                           | 1            | <table><tr><td>...</td></tr><tr><td>...</td></tr><tr><td>value</td></tr></table>  | <table><tr><td>...</td></tr><tr><td>...</td></tr><tr><td>value</td></tr></table>   | выставляет флаги N (negative) и Z (zero) для value                                                                                                                                             |
| INC<br/>DEC                                                     | 1            | <table><tr><td>...</td></tr><tr><td>...</td></tr><tr><td>value</td></tr></table>  | <table><tr><td>...</td></tr><tr><td>...</td></tr><tr><td>result</td></tr></table>  | выполняет инкремент или декремент                                                                                                                                                              |
| READ [port]                                                     | 1            | <table><tr><td>...</td></tr><tr><td>...</td></tr><tr><td>...</td></tr></table>    | <table><tr><td>...</td></tr><tr><td>...</td></tr><tr><td>value</td></tr></table>   | читает из порта один символ                                                                                                                                                                    |
| WRITE [port]                                                    | 1            | <table><tr><td>...</td></tr><tr><td>...</td></tr><tr><td>value</td></tr></table>  | <table><tr><td>...</td></tr><tr><td>...</td></tr><tr><td>...</td></tr></table>     | записывает вершину стека в порт                                                                                                                                                                |
| DUP                                                             | 1            | <table><tr><td>...</td></tr><tr><td>...</td></tr><tr><td>value</td></tr></table>  | <table><tr><td>...</td></tr><tr><td>value</td></tr><tr><td>value</td></tr></table> | дублирует значение с вершины стека                                                                                                                                                             |
| SWAP                                                            | 1            | <table><tr><td>...</td></tr><tr><td>a</td></tr><tr><td>b</td></tr></table>        | <table><tr><td>...</td></tr><tr><td>b</td></tr><tr><td>a</td></tr></table>         | меняет местами верхние 2 значения в стеке                                                                                                                                                      |
| JUMP [len]<br/>JZ [len]<br/>JNZ [len]<br/>JP [len]<br/>JM [len] | 1            | -                                                                                 | -                                                                                  | прыжок на указанное расстояние на основании выставленных флагов. <br/>JUMP - безусловный, <br/>JZ - прыжок, если ноль, <br/>JNZ - прыжок, если не ноль, , <br/>JP/JM - прыжок, если плюс/минус |
| CALL [addr]                                                     | 1            | -                                                                                 | -                                                                                  | вызов функции по адресу addr                                                                                                                                                                   |
| RET                                                             | 1            | -                                                                                 | -                                                                                  | возврат из функции                                                                                                                                                                             |
| HALT                                                            | 1            | -                                                                                 | -                                                                                  | остановить выполнение                                                                                                                                                                          |


## Формат инструкций
Инструкции представлены в формате _JSON_ по заданию
```json
{
  "index": 1,
  "opcode": "push",
  "arg": 123,
  "term": "defvar"
}
```
где:
- `opcode` - код операции (Opcode - тип данных, определенный в [isa](isa.py))
- `arg` - аргумент инструкции
- `term` - указывает на то, к какой части исходного кода относится инструкция

# Транслятор
Интерфейс командной строки: `python translator.py <input_file> <target_file>`

Транслятор реализован в модуле [translator](translator.py)

Этапы трансляции:
1. удаление комментариев
2. определение строковых литералов и замена их на заглушки
3. форматирование программы (удаление двойных пробелов и пр.)
4. парсинг программы: исходный код представляется как вложенные объекты класса `Expression` (определен в [translator](translator.py), попутная проверка на корректность скобочной последовательности)
5. генерация машинного кода на основе объектов `Expression`, попутная проверка корректности использования синтаксических конструкций языка
6. сериализация - представление в формате _JSON_






