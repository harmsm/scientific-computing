==============================
CH410/510 Scientific Computing
==============================

Overview
========

+ The class will meet Monday and Wednesday at 9 am 1 hr, and then Friday at 9 am for 2 hr.

+ All classwork will be done remotely. `Details are here <remote.html>`_.

+ Details regarding grading and course policies are in the `syllabus <syllabus.html>`_.

Getting help
============

`Python reference and links to helpful material <cheat-sheet.html>`_

Office hours:
-------------

Check slack :code:`#general` channel for zoom links to office hours.

+ Anneliese: 4 pm on Mondays
+ Luis: 11 am on Wednesdays
+ Michael: 2 pm on Wednesdays
+ Joseph: 2 pm on Thursdays
+ Mike: 1 pm on Fridays

Getting set up:
---------------

+ To get your environment set up, please follow `these instructions <https://python-for-scientists.readthedocs.io/en/latest/_pages/install_python.html>`_.

+ To test your environment, please try to run this `jupyter notebook <https://github.com/harmsm/pythonic-science/raw/master/test_notebook.ipynb>`_ (right-click to save onto your computer.)



Schedule and course materials
=============================

*Warning*: Future dates and material may be subject to (minor) change.

In general, Mon and Wed will be instruction days where we cover new programming
material.  Fri will be an open "lab" where you will work on exercises in groups.

.. table::
    :widths: 10 45 15 15 15

    +-------+------------------------------------------------+----------------------------------+------------------------------------------------------------+------------+
    | Date  | Topic                                          | Preclass                         | Due                                                        | Postclass  |
    +=======+================================================+==================================+============================================================+============+
    | 3/30  | Introduction. Configuring jupyter and python   |                                  |                                                            | `class1`_  |
    +-------+------------------------------------------------+----------------------------------+------------------------------------------------------------+------------+
    | 4/1   | The jupyter notebook. Python as a calculator.  | + `test_notebook`_               | + `config_environment`_                                    | `class2`_  |
    |       |                                                | + `chapter_00`_                  | + Take the `survey`_ if you haven't.                       |            |
    +-------+------------------------------------------------+----------------------------------+------------------------------------------------------------+------------+
    | 4/3   | Conditionals, loops, lists, arrays.            | `lab_00_0`_                      |                                                            |            |
    +-------+------------------------------------------------+----------------------------------+------------------------------------------------------------+------------+
    | 4/6   | Functions and namespace                        |                                  |                                                            |            |
    +-------+------------------------------------------------+----------------------------------+------------------------------------------------------------+------------+
    | 4/8   | Graphing and matplotlib                        |                                  |                                                            |            |
    +-------+------------------------------------------------+----------------------------------+------------------------------------------------------------+------------+
    | 4/10  | Lab: programming puzzles.                      | `lab_00_1`_                      | `lab_00_0`_                                                |            |
    +-------+------------------------------------------------+----------------------------------+------------------------------------------------------------+------------+
    | 4/13  | Simulation                                     | `chapter_01`_                    |                                                            |            |
    +-------+------------------------------------------------+----------------------------------+------------------------------------------------------------+------------+
    | 4/15  | Simulation                                     |                                  | `lab_00_1`_                                                |            |
    +-------+------------------------------------------------+----------------------------------+------------------------------------------------------------+------------+
    | 4/17  | Lab: simulating an experiment.                 | `lab_01`_                        |                                                            |            |
    +-------+------------------------------------------------+----------------------------------+------------------------------------------------------------+------------+
    | 4/20  | Fitting models to data                         | `chapter_02`_                    |                                                            |            |
    +-------+------------------------------------------------+----------------------------------+------------------------------------------------------------+------------+
    | 4/22  | Fitting models to data                         |                                  | `lab_01`_                                                  |            |
    +-------+------------------------------------------------+----------------------------------+------------------------------------------------------------+------------+
    | 4/24  | Lab: fitting models to data                    | `lab_02`_                        |                                                            |            |
    +-------+------------------------------------------------+----------------------------------+------------------------------------------------------------+------------+
    | 4/27  | Intro to machine learning                      | chapter_04                       |                                                            |            |
    +-------+------------------------------------------------+----------------------------------+------------------------------------------------------------+------------+
    | 4/29  | Classification with machine learning           |                                  | `lab_02`_                                                  |            |
    +-------+------------------------------------------------+----------------------------------+------------------------------------------------------------+------------+
    | 5/1   | Lab: classification using machine learning     | lab_04                           |                                                            |            |
    +-------+------------------------------------------------+----------------------------------+------------------------------------------------------------+------------+
    | 5/4   | Molecular structures                           | chapter_03                       |                                                            |            |
    +-------+------------------------------------------------+----------------------------------+------------------------------------------------------------+------------+
    | 5/6   | Molecular structures                           |                                  | lab_04                                                     |            |
    +-------+------------------------------------------------+----------------------------------+------------------------------------------------------------+------------+
    | 5/8   | Lab: calculating structural properties         | lab_03                           | `prospectus`_                                              |            |
    +-------+------------------------------------------------+----------------------------------+------------------------------------------------------------+------------+
    | 5/11  | Big(ish) data                                  | chapter_05                       |                                                            |            |
    +-------+------------------------------------------------+----------------------------------+------------------------------------------------------------+------------+
    | 5/13  | Big(ish) data                                  |                                  | lab_03                                                     |            |
    +-------+------------------------------------------------+----------------------------------+------------------------------------------------------------+------------+
    | 5/15  | Lab: analyzing HTS data                        | lab_05                           |                                                            |            |
    +-------+------------------------------------------------+----------------------------------+------------------------------------------------------------+------------+
    | 5/18  | Working with images                            | chapter_06                       |                                                            |            |
    +-------+------------------------------------------------+----------------------------------+------------------------------------------------------------+------------+
    | 5/20  | Working with images                            |                                  | lab_05                                                     |            |
    +-------+------------------------------------------------+----------------------------------+------------------------------------------------------------+------------+
    | 5/22  | Lab: analyzing microscopy images               | lab_06                           |                                                            |            |
    +-------+------------------------------------------------+----------------------------------+------------------------------------------------------------+------------+
    | 5/25  | Memorial day, no class                         |                                  |                                                            |            |
    +-------+------------------------------------------------+----------------------------------+------------------------------------------------------------+------------+
    | 5/27  | Final project, in-class work                   |                                  | lab_06                                                     |            |
    +-------+------------------------------------------------+----------------------------------+------------------------------------------------------------+------------+
    | 5/29  | Final project, in-class work                   |                                  |                                                            |            |
    +-------+------------------------------------------------+----------------------------------+------------------------------------------------------------+------------+
    | 6/1   | Final project, in-class work                   |                                  |                                                            |            |
    +-------+------------------------------------------------+----------------------------------+------------------------------------------------------------+------------+
    | 6/3   | Final project, in-class work                   |                                  |                                                            |            |
    +-------+------------------------------------------------+----------------------------------+------------------------------------------------------------+------------+
    | 6/5   | Final project, in-class work                   |                                  |                                                            |            |
    +-------+------------------------------------------------+----------------------------------+------------------------------------------------------------+------------+
    | 6/8   | Final project due                              |                                  | `final_project`_                                           |            |
    +-------+------------------------------------------------+----------------------------------+------------------------------------------------------------+------------+

.. all links
.. _`test_notebook`: https://github.com/harmsm/pythonic-science/raw/master/test_notebook.ipynb
.. _`chapter_00`: https://github.com/harmsm/pythonic-science/raw/master/zips/chapters/00_inductive-python.zip
.. _`lab_00_0`: https://github.com/harmsm/pythonic-science/raw/master/zips/labs/00.0_python-practice.zip
.. _`lab_00_1`: https://github.com/harmsm/pythonic-science/raw/master/zips/labs/00.1_programming-puzzles.zip
.. _`chapter_01`: https://github.com/harmsm/pythonic-science/raw/master/zips/chapters/01_simulation.zip
.. _`lab_01`: https://github.com/harmsm/pythonic-science/raw/master/zips/labs/01_simulation.zip
.. _`chapter_02`: https://github.com/harmsm/pythonic-science/raw/master/zips/chapters/02_regression.zip
.. _`lab_02`: https://github.com/harmsm/pythonic-science/raw/master/zips/labs/02_regression.zip
.. _`config_environment`: https://python-for-scientists.readthedocs.io/en/latest/_pages/install_python.html
.. _`survey`: https://forms.gle/XMfB2a9tpuuGeydY8
.. _`prospectus`: https://harmsm.github.io/scientific-computing/final-project.html
.. _`final_project`: https://harmsm.github.io/scientific-computing/final-project.html
.. _`class1`: https://harmsm.github.io/scientific-computing/non-sphinx/sessions/00/index.html
.. _`class2`: https://harmsm.github.io/scientific-computing/non-sphinx/sessions/01/index.html

.. toctree::
   syllabus
   remote
   final-project
   cheat-sheet
   :maxdepth: 2
   :caption: Sections:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
