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

Bisecting a Line
-----------------

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


Intersecting Two Lines
```````````````````````

To calculate the intercepts we'll describe the lines and segments as vectors with one independent variable.

.. math::
    \begin{aligned}
    \vec{l}(t) &= \vec{p}_0+(\vec{p}_1-\vec{p}_0)*t \\
    &= \vec{p}_0 + \vec{v}*t
    \end{aligned}

Since segments have a defined start and end, t is valid over a closed range :math:`t \in [0,1]`. Lines on the other hand extend infinitely in all directions, so t can be any real number. For convenience I'm going to refer to our line segments as :math:`\vec{g}(t) = \vec{p_0} + \vec{v}_0t`, and the dividing line as :math:`l(s) = \vec{p}_1 + \vec{v}_1 s`. We're interested in the value t where the two lines meet.

.. math::
    \begin{aligned}
    \vec{g}(t) &= \vec{l}(s) \\
    \vec{p_0} + \vec{v}_0 t &= \vec{p}_1 + \vec{v}_1 s \\
    &...
    \end{aligned}\\
    t = \frac{(\vec{p}_1-\vec{p}_0) \times \vec{v}_1}{\vec{v}_0 \times \vec{v}_1}

I've skipped a few steps in the above equation because the intercept of two vector equations is well understood. What we're more interested in is using the results to determine where the segments lie with respect to our line. Red flags might be going off because this equation is dividing two vectors, which is (1) an invalid operation, and (2) can't result in a scaler. Since our lines and segments are all 2D, however, we're going to use the 2D definition of cross product: :math:`\vec{A} \times \vec{B} = A_x*B_y-A_y*B_x`. This scaler is the z-component of the cross product vector we *would* have gotten had we taken a traditional 3D cross-product and set the z-values to zero for A & B. 

Ahead, Behind, Bisected or Colinear
``````````````````````````````````````

It's easy to tell that the line bisects a given segment when the t is between 0 and 1. What about the other cases though: how do we determine if the segment is in front or behind the line, and what about cases where t is undefined? To get more insight into what's happening with the intersection equation, we'll look at the numerator and denominator separately.

Numerator
    We already defined the two-dimensional vector cross product: :math:`\vec{A} \times \vec{B} = A_x*B_y-A_y*B_x`. Taking a closer look, it's identical to :math:`(A_x, A_y) \cdot (B_y, -B_x)`, and :math:`(B_y, -B_x)` is the same as rotating :math:`(B_x,B_y)` clockwise 90 degrees, aka it's *proportional to the normal vector we defined above*. The numerator can be rewritten as:

    .. math::

        ((\vec{p}_0-\vec{p}_1) \cdot \hat{n})|\vec{v}_1|


    Meaning the numerator is taking the distance between two a point on the segment and a point on the line, and projecting that vector onto the normal vector of the line (this is identical to calculating the `shortest distance between a point and a line`_). From our definition of "in front" and "behind", we can claim that a line segment is *partially* in front of the line if the numerator is > 0, and *partially* behind if the numerator is < 0. If the numerator is equal to zero, it means the first point of the segment is on the line, and we need to look at the denominator to define whether it's in front or behind.

.. _`shortest distance between a point and a line`: https://en.wikipedia.org/wiki/Distance_from_a_point_to_a_line

Denominator
    Using the same logic as above, the denominator can be rewritten as a vector projection onto the normal vector:

    .. math::

        -(\vec{v}_0 \cdot \hat{n})|\vec{v}_1|

    This projection is a measure of how far :math:`\hat{g}(t)` travels towards line \hat{l}(s) per interval t. Since the numerator is how far the lines are apart (projected onto the normal vector), and the denominator is how fast one line is approaching the second along that same normal, it makes sense that the ratio is the amount of time (t) until they intersect! If the denominator is equal to zero, the two lines are parallel, and the sign of the numerator determines where the segment lies relative to the line. 

With the exception of cases where t is between 0 & 1, the numerator and denominator must be considered when defining the segments location. A summary of all cases is given below:

* :math:`0 < t < 1` -  The segment is bisected by the line at t.

* :math:`NUM > 0 \&\& (t > 1 || t < 0)` - The segment is in front of the line.

* :math:`NUM < 0 \&\& (t > 1 || t < 0)` - The segment is behind the line.

* :math:`t = 0` -  The origin of the segment is on the line. If the denominator is < 0 the segment is in front of the line. If it is > 0 the segment is behind the line. 

* :math:`DEN = 0` - The segment is parallel to the line. If the numerator is positive, the segment is in front of the line. If the numerator is negative, the segment is behind the line. If the numerator is zero, the segment is colinear to the line.

With these cases we're ready to implement the first half of the bisect function. Right now all it does is build a set of boolean masks used to index the segment array. before returning the new segments we need to write some code to split bisected segments into two new segments. Notice how when calculating t the denominator has an extra component :code:`parallel`. This boolean value is cast as a 1 if the denominator would have been zero, and prevents Numpy from throwing a warning about divide by zero errors.

.. include:: files/bsp_2d/bisect_stub.py
    :code: python


Handling Bisected Lines
````````````````````````

If a segment is bisected by the line at time t, we need to create two new segments, one from 0-t, and a second from t-1. Fancy indexing with Numpy can be slower than doing simple operations on an entire array (this is highly dependent on the application), so we'll create two new segments for every segment and then filter.

.. code:: python

    intersection_points = segment_start + intersection[..., np.newaxis] * v0
    l_segments = np.stack((segments[..., 0, :], intersection_points), axis=1)
    r_segments = np.stack((intersection_points, segments[..., 1, :]), axis=1)

Notice how they're split into l_segments and r_segments, not 'in front' and 'behind'. That's because right now we don't know which segments are which, and need to filter them based on the numerator. If the numerator is >0, the first point of the segment is ahead of the line, therefore the l_segment is ahead and the r_segment is behind. 

.. code:: python

    mask = numerator[..., np.newaxis, np.newaxis] > 0
    bisected_ahead = np.where(mask, l_segments, r_segments)[bisected]
    bisected_behind = np.where(np.logical_not(mask), l_segments, r_segments)[bisected]

At this point we've used fancy indexing to keep only the bisected segments. All that's left to do is combine the bisected segments with their respective ahead/behind sets, and return the three sets of segments. The full function is found here_, with a set of if statements to catch cases where ahead/behind sets are empty arrays. The :code:`Tuple` Typehint is from the typing_ module, and is useful for IDE's to infer what types the function will return.

.. _typing: https://docs.python.org/3/library/typing.html
.. _here: https://github.com/rfrazier716/bsp/blob/12af4fba95cc594b2f3da604491de75d508d1d58/bsp.py#L9

Recursively Building a BSP Tree
--------------------------------

Compared to the amount of code required to partition our line segments, the function build the BSP tree is relatively simple.

.. include:: files/bsp_2d/build_tree.py
    :code: python

Let's pick it apart, starting with the function signature:

.. code:: python

    def build_tree(segments: np.ndarray, starting_segment: np.ndarray = None) -> nx.DiGraph:

The function expects a nx2x2 array of line segments, and an optional starting segment that it used as the first dividing line. The output will be a NetworkX directed graph object where ever node is a dividing line holding the colinear segments for that line.

.. code:: python

    graph = nx.DiGraph()  # make a new directed graph
    if starting_segment is None:
        starting_segment = segments[0]

    # run the recursive helper function, which should add all nodes and edges
    bsp_helper(segments, starting_segment)
    return nx.relabel.convert_node_labels_to_integers(graph)

Here we create the actual graph object and check if the user provided a starting segment, if no segment was given the first segment of the array is used instead. The function then calls a *nested* bsp helper function that fills the graph with divided segments, and then relabels all nodes sequentially before returning the graph.

Defining bsp_helper within build_tree allows it to access the graph variable defined in build_tree without explicitly passing it (this is part of the `enclosing scope`_ in an LEBG model). It also keeps bsp_helper out of the module namespace. 

.. _`enclosing scope`: https://realpython.com/python-namespaces-scope/#variable-scope

.. code:: python

    def bsp_helper(segments: np.ndarray, division_line: np.ndarray):
        ahead, behind, colinear = bisect(segments, division_line)  # get the bisected segments
        node_id = id(division_line)  # a hashable value for the node
        graph.add_node(node_id, line=division_line, colinear_segments=colinear)  # add the node to the graph
        if behind.size != 0:  # if there's any elements behind
            node_behind = bsp_helper(behind, behind[0])  # recursively call for all segments behind
            graph.add_edge(node_id, node_behind, position=-1)  # add an edge from this node to the behind node
        if ahead.size != 0:
            node_ahead = bsp_helper(ahead, ahead[0])  # recursively call for all segments in front
            graph.add_edge(node_id, node_ahead, position=1)  # add an edge from this node to the front node
        return node_id  # return the hashed id

The helper function calculates where each segment in a set falls relative to the dividing line. It then creates a new node with two attributes: the dividing line of the node, and any segments that are colinear to that dividing line. If there's any segments in front of the line, the helper function recursively calls itself with only the set of segments ahead of current dividing line, returning the id of the created node. The returned node is connected to the current node with an edge, whose position attribute is +1 (meaning it's ahead of the current node). The same is then done for segments behind the current line. If recursive functions are a new concept, RealPython has a `great tutorial`_ on understanding and implementing them, as well as introduces the `@lru_cache`_ decorator.

.. _`great tutorial`: https://realpython.com/python-thinking-recursively/
.. _`@lru_cache`: https://docs.python.org/3/library/functools.html#functools.lru_cache 

Potential Applications
========================

Constructive Solid Geometry
----------------------------

3D Rendering
-------------







