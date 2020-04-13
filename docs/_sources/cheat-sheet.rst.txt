
Python quick reference
======================

Resources
---------

General python resources
........................

* `socratica youtube channel <http://bit.ly/PythonSocratica>`_: an amazing set of introductory python videos.
* `insane python cheat sheet <https://perso.limsi.fr/pointal/_media/python:cours:mementopython3-english.pdf>`_: most of python syntax, all on one two-sided sheet.
* `python gotchas <http://docs.python-guide.org/en/latest/writing/gotchas/>`_: things that tend to trip up python programmers.
* `python style guide <https://www.python.org/dev/peps/pep-0008/>`_: rules for writing python code so other people can actually read it.
* `plotting reference <https://github.com/harmsm/pythonic-science/raw/master/reference/plotting_reference.ipynb>`_: Jupyter notebook showing a bunch of matplotlib functionality (right click to save jupyter notebook).
* `codeacademy <https://www.codecademy.com/>`_: great resource for learning python syntax and basic concepts.  Free 7-day trial.  Looks like there might be free plans for students.

Jupyter resources
.................

* `jupyter reference <https://github.com/harmsm/pythonic-science/raw/master/reference/jupyter_reference.ipynb>`_: Jupyter notebook showing off what you can do in notebooks (right click to save jupyter notebook)
* `jupyter keyboard shortcuts <https://towardsdatascience.com/jypyter-notebook-shortcuts-bf0101a98330>`_: Keyboard shortuts for jupyter for those of us that hate our mice
* `changing jupyter startup folder <https://medium.com/@kegui/change-jupyter-notebook-startup-folder-windows-608dfcfdc104>`_: Convenient way to change startup folder for windows, the guide for mac is okay too

Scientific-python resources
...........................

* `fitting and summary of quality-of-fit measures <http://connor-johnson.com/2014/02/18/linear-regression-with-python/>`_: resource for doing fitting in python.


Comparison operators
--------------------

Used to compare two objects.  Returns :code:`True` or :code:`False`.

 + :code:`x < y` (less than)
 + :code:`x <= y` (less than or equal to)
 + :code:`x > y` (greater than)
 + :code:`x >= y` (greater than or equal to)
 + :code:`x == y` (is equal to)
 + :code:`x != y` (is not equal to)

These can be combined using :code:`and` and :code:`or`.

**Example**

.. code-block:: python

    x = 0
    y = 5

    if x < y:
        print("x is smaller than y")

    if (x < y) and (x < 1):
        print("x is smaller than y and x is less than 1")

Conditionals
------------

.. code-block:: python

    if condition_one:
        do_something
    elif condition_two:
        do_something_else
    elif condition_three:
        do_another_thing
    else:
        do_yet_another_thing

where :code:`condition_one`, :code:`condition_two` and :code:`condition_three`
are things that can be read as :code:`True` or :code:`False`.  `else` is run if
none of the other conditions are met.  If multiple conditions are met, only the
first one is executed.

**Example**

.. code-block:: python

    x = 2
    if x < 0:
        print("x is negative")
    elif x == 0:
        print("x is zero")
    elif x > 0 and x < 100:
        print("x is positive but less than 100")
    else:
        print("x is bigger than 100")

Loops
-----

:code:`for` syntax
..................



.. code-block:: python

    for x in iterator:
        something_to_x

where :code:`iterator` is something like :code:`range(10)` or a list that has
multiple entries.

**Example**

.. code-block:: python

    for i in range(10):
        print(i)

:code:`while` syntax
....................

.. code-block:: python

    while condition:
        something

where :code:`condition` is something that can be read as :code:`True` or
:code:`False`

**Example**

.. code-block:: python

    i = 0
    while i < 10:
        print(i)
        i = i + 1



.. warning::

    If you forgot the :code:`i = i + 1` line in the code above, it would create
    and infinite loop and your code would freeze.  This is a common mistake
    when using :code:`while` loops.

:code:`continue` and :code:`break` syntax
.........................................

+ :code:`continue` hops to the next iteration of the loop
+ :code:`break` terminates the loop

**Example**

.. code-block:: python

    # Will print i from 6 to 90
    i = 0
    while i < 100:
        i = i + 1
        if i < 5:
            continue

        if i > 90:
            break

        print(i)

Datatypes
---------

Single-value datatypes
......................

+ :code:`int` (integer)
+ :code:`bool` (True or False)
+ :code:`float` (decimal number)

List-like objects
.................

:code:`list`
''''''''''''
+ **Specs**:
 * collection of arbitrary objects
 * indexed by number (starting from 0)
+ **Creating new**:
 * :code:`some_list = []` creates a new, empty list
 * :code:`some_list = [1,2,3]` creates a new list with three entries
+ **Adding new entry**:
 * :code:`some_list.append(1)` appends the integer :code:`1` to the end of the
   list
 * :code:`some_list.append({})` appends an empty dictionary to the end of the
   list
+ **Remove entry**:
 * :code:`some_list.pop(1)` returns the second entry and removes it from the
   list
+ **Getting values**:
 * :code:`some_list[0]` gives first entry in list
 * :code:`some_list[-1]` gives last entry in list
 * :code:`some_list[1:3]` gives the second and third entry in list
+ **Setting values**:
 * :code:`some_list[0] = 5` sets the first value to :code:`5`
 * :code:`some_list[-1] = 5` sets the last value to :code:`5`
 * :code:`some_list[1:3] = ["test",8]` sets the second and third entries to
   :code:`"test"` and :code:`8`, respectively.

:code:`tuple`
'''''''''''''

+ **Specs**:
 * collection of arbitrary objects
 * behaves just like a list *except* that once it is created it cannot be
   modified.
+ **Creating new**:
 * :code:`some_tuple = (1,2,3)` creates a new tuple
+ **Adding new entry**: can't be done
+ **Remove entry**: can't be done
+ **Getting values**:
 * Indexing and slicing rules just like lists
+ **Setting values**: can't be done

:code:`dict`
''''''''''''

+ **Specs**:
 * collection of arbitrary objects
 * objects are indexed by keys
 * keys can be almost any type *except* lists and dictionaries.
 * dictionaries are not ordered, meaning that if you loop through them
   more than once, the items could pop out in a different order
+ **Creating new**:
 * :code:`some_dict = {}` creates a new, empty dictionary
 * :code:`some_dict = {"cows":27,18:"dogs"}` creates a new dictionary with
   :code:`"cows"` keying to the value :code:`27` and :code:`18` keying to the
   value :code:`"dogs"`
+ **Adding new entry**:
 * :code:`some_dict["meddling"] = "kids"` creates a key/value pair where the
   key :code:`"meddling"` gives the value :code:`"kids"`
+ **Remove entry**:
 * :code:`some_dict.pop("meddling")` would return :code:`"kids"` and remove
   the :code:`"meddling/kids"` key/value pair from the dictionary
+ **Getting values**:
 * :code:`some_dict["meddling"]` would return :code:`"kids"`
 * :code:`list(some_dict.keys())` returns list of keys
 * :code:`list(some_dict.values())` returns list of values
 * :code:`list(some_dict.items())` returns list of tuples with all key/value
   pairs
+ **Setting values**:
 * :code:`some_dict["scooby"] = "doo"` would key the value "doo" to the key
   :code:`"scooby"`

:code:`string`
''''''''''''''
+ **Specs**:
 * stores text
 * behaves similarly to a list where every entry is a character
+ **Creating new**:
 * :code:`some_string = "test"` creates a new string storing test
 * Note that text in the string must have :code:`"` around it.
+ **Adding new entry**: can't be done
+ **Removing entry**: can't be done
+ **Getting values**: just like a list
 * :code:`some_string[0]` returns the first letter
 * :code:`some_string[-1]` returns the last letter
 * :code:`some_string[1:3]` returns the second and third letter
+ **Setting values**: just like a list
 * :code:`some_string[0] = "c"` sets the first letter to :code:`"c"`

:code:`numpy.array`
'''''''''''''''''''
+ **Specs**:
 * collection of numerical objects of the same type
 * less flexible than a list (all objects must be same type, can't change
   dimensions after created).
 * collection of numpy functions allow extremely fast enumeration and access
 * requires :code:`import numpy` at top of program
+ **Creating**:
 * :code:`numpy.zeros((10,10),dtype=int)` creates a new 10x10 integer array of
   zeros
 * :code:`numpy.array([1.0,1.3,2.3],dtype=float)` creates a new 3 entry array
   of floats with input list values
+ **Adding new entry**:
 * Can't really be done
 * :code:`y = numpy.append(x,1.0)` will create a copy of `x` with 1.0 appended
   to it.
+ **Removing entry**:
 * Can't really be done
 * :code:`y = numpy.delete(x,0)` will create a copy of `y` with the first
   element removed.
+ **Getting values**:
 * Extremely powerful (and sometimes complex)
 * :code:`x[0]` returns the
 * :code:`x[0,0,0]` returns the bottom left corner of a 3d array
 * :code:`x[0:5]` returns the first five entries in a 1d array
 * :code:`x[0,:]` returns the whole first column of a 2d array
 * :code:`x[:,:,:,2]` returns a 3d slice at the third position on along the
   fourth dimension of a 4d array
+ **Setting values**:
 * Exact same indexing and slicing rules as getting values

Libraries
---------

Libraries are extensions of basic python that provide expanded functionality.
To get access to a library, add a line like:

.. code-block:: python

    import math

You can then run this:

.. code-block:: python

    print(math.sin(1))

You can assign imported modules more convenient names.  For example, the
following would do exactly the same as the above program.

.. code-block:: python

    import math as m
    print(m.sin(1))

You can also import functions (and other objects) from each module using the
`from` syntax:

.. code-block:: python

    import math
    from math import sin
    print(sin(1))


Important libraries:
....................

+ math (math functions)
+ random (generate random numbers)
+ numpy (fast arrays and some math functions)
+ pandas (dataframes in python)
+ matplotlib (used for making complex plots)
+ scipy (tons of scienc-y extensions of python)
+ os (used for doing things like listing files in a directory
+ combinations (used to make combinations and permutations efficiently)

Functions
---------

Functions are blocks of re-usable code that take arguments and return values.

Functions are defined using the `def` keyword.  Anything indented under `def`
is part of the function.

.. code-block:: python

    def my_function(x):

        a = x + 2

        return a*5

    z = 5
    print(my_function(z))


Variables defined inside the function cannot be accessed outside of that
function.  :code:`a` from the function above is created and destroyed
every time the function is run.

.. warning::

    Functions "know" about variables outside the function.  If I used :code:`z`
    inside of :code:`my_function`, the program would run fine.  This is a **bad**
    idea because :code:`z` is then implicitly defined.  I could get a different
    result if I run :code:`my_function(5)` **Always** pass in variables as
    arguments (like :code:`x` above) rather than accessing them implicitly.


pandas
------

Construction
............

.. code-block:: python

    # column-centric construction
    import pandas as pd
    df = pd.DataFrame({"col1":[v1,v2,...],"col2":[vi,vj,...],...})

.. code-block:: python

    # Read from csv
    df = pd.read_csv("some_csv_file.csv")

    # Read from excel
    df = pd.read_excel("some_excel_file.xlsx")

Writing out
...........

.. code-block:: python

    df.to_excel("some_excel_file.xlsx")
    df.to_csv("some_csv_file.csv")

Accessing data
..............

+ :code:`df.iloc[i,j]` accesses the ith row and jth column in the data frame.
 * :code:`iloc[i,j]` will **always refer to the same place in the data
   frame.** :code:`iloc[0,0]` is the top-left, :code:`iloc[n_row-1,n_col-1]` is
   the bottom-right.
 * :code:`iloc[i,j]` will *not* always refer to the same data.  If you
   delete or reorder rows and columns, different data could be
   in each cell.
+ :code:`df.loc['x','y']`:
 * :code:`loc['x','y']` will **always refer to the same data.**  This
   is true even if you delete or reorder rows and columns.
 * :code:`loc['x','y']` will **not** always refer to the same place
   in the data frame.

.. warning::
    :code:`pandas` DataFrames often have rows whose indexes are numbers.
    :code:`df = pd.DataFrame({"col1":[1,2,3],"col2":[4,5,6]})` will yield a
    dataframe where the rows are named :code:`0,1,2`. If we delete row
    :code:`0`, rows :code:`1` and :code:`2` will still be accessed by
    :code:`loc[1,:]` and :code:`loc[2,:]`.

+ You can slice a pandas DataFrame like a numpy array.

+ Both :code:`iloc` and :code:`loc` can be used for setting values:

    .. code-block:: python

        df = pd.DataFrame({"col1":[1,2,3],"col2":[4,5,6]})
        df.loc[1,"col1"] = 17 # set row 1, "col1" (the 2 above) to 17
        df.iloc[1,1] = 23 # set the second row, second column (the 5 above) to 17
