.. title: 2D Binary Spacing Partitioning with Python and NetworkX
.. slug: 2d-binary-spacing-partitioning-with-python-and-networkx
.. date: 2021-03-29 20:20:56 UTC-04:00
.. tags: 
.. category: 
.. link: 
.. description: 
.. type: text
.. has_math: true
.. status: published

I'm a sucker for tricks programmers use to get games to run efficiently, from the metro train in Fall Out 3 that's actually a piece of armor, to the spell casting rabbits in World of Warcraft that triggered world events. In a slightly different camp, however, are tricks that enabled game makers to do the impossible with the hardware they're given, and ...

table of contents goes here

What's So Special About Binary Space?
======================================

Add details about how it works and uses


Creating a BSP Tree
=============================

Creating a BSP tree requires a recursive algorithm that constructs it in a depth-first manner, outlined below.

1. Calculate the intersection of the dividing line with all segments .
2. Split any segments that intersect the dividing line into two segments at the intersection.
3. Add colinear line segments to the current node of the tree.
4. Create a new child node and repeat steps 1-6 for all segments in front of the dividing line..
5. Create a new child node and repeat steps 1-6 for all segments behind the dividing line
6. Connect the new nodes to the current node with an edge.

Notice that steps 4 and 5 repeat every step up to and *including* themselves. This recursion builds the tree depth first... something something

Setting up the Environment
---------------------------

In addition to the standard library, we'll use Numpy for calculating the line-segment intersections, and NetworkX to create the tree. NetworkX is a general purpose graph library, and will prevent us from having to define our own nodes and edges. Additionally, it includes extensive traversal algorithms and can be combined with GraphViz for visualization of tree. Both packages are installable via pip.

.. code:: shell

    py -m pip install numpy, networkx

Ahead, Behind, Bisected or Colinear
------------------------------------

The bulk of the processing is determining where each line segment in a set intersects the dividing line. We'll make a function called :code:`bisect` that accepts an array of line segments and a dividing line, and returns three arrays, one each for segments ahead, behind, and colinear to the dividing line.

.. code:: python

    def bisect(segments: np.ndarray, line: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        # separates a set of line segments based on where they intercept a dividing line

The segments array is an Nx2x2 array, where N is the number of segments being sorted. Each row of the array is a set of two xy-pairs, for the start and endpoints of the line segment. For example, a square centered at the origin is composed of four segments:

.. code:: python

    square = np.ndarray([
        [[1,-1],[-1,-1]],
        [[-1,-1],[-1,1]],
        [[-1,1],[1,1]], 
        [[1,1],[1,-1]]
    ])

Similarly, a line is represented by a single 2x2 array of two XY-pairs. An alternative method for defining segments and lines involves an Nx2 array with all points the segments are made up of. The segment array then becomes an nx2 array of *indexes*, identifying which two points make up a a given segment. With this method, the square example from above would become: 

.. code:: python

    points = np.ndarray([
        [1,-1],
        [-1,-1],
        [-1,1],
        [1,1]
    ])

    square = np.ndarray([
        [1,2],
        [2,3],
        [3,4],
        [4,1]
    ])

Apart from the overhead of having to manage two arrays, this approach is more efficient and easier to type without errors, but less obvious about what your shape looks like without referencing the point array. Regardless of method used to store segments, the advantage of using Numpy data structures instead of lists and tuples is that we can apply the intersection algorithm to the entire segment array at once, instead of iterating over each segment with a for loop. Since Numpy calls compiled C-code, there is almost always a performance gain when a for loop can be replaced with array operators.

The last decision we need to make before writing the bisect function is come up with a consistent definition for what "in front" and "behind" mean in the context of our lines. An easy enough way to visualize it is this: If you take your right hand and orient it so that the pad of your hand is on top of the first segment, and your fingers point towards the second, everything on the left side of your hand (closest to the palm) is in front of the line, and everything on the right side (closes to the back of your hand) is behind the line. Phrased more formally, this is an extension of the `right hand rule`_. We're defining a normal vector (:math:`\hat{n}`) to the line (:math:`\hat{l}`) such that :math:`\hat{l} \times \hat{n} \propto \hat{z}`, where :math:`\hat{z}` is the z-axis (extending out of the page in our case). A point (:math:`\vec{p}`) is in front of the line if the projection of the vector from any point on the line (:math:`\vec{q}`) to :math:`\vec{p}` onto the normal is greater than zero.

.. math::

    (\vec{p}-\vec{q}) \cdot {\hat{n}} > 0


.. _`right hand rule`: https://en.wikipedia.org/wiki/Right-hand_rule

Lines as Vectors
```````````````````````

Intersecting Two Lines
```````````````````````

Recursive Function
-------------------

Potential Applications
========================

Constructive Solid Geometry
----------------------------

3D Rendering
-------------







