.. title: 2D Binary Spacing Partitioning with Python and NetworkX
.. slug: 2d-binary-spacing-partitioning-with-python-and-networkx
.. date: 2021-03-29 20:20:56 UTC-04:00
.. tags: python, numpy, graphics
.. category: 
.. link: 
.. description: 
.. type: text
.. has_math: true
.. status: published
.. previewimage: /images/bsp_2d/opengraph.png

I'm a sucker for tricks programmers use to get games to run efficiently, from the `metro train in Fall Out 3`_ that's actually a piece of armor, to the `spell casting bunnies`_ in World of Warcraft that triggered world events. In a slightly different camp, however, are tricks that enabled game makers to do the impossible with the hardware they're given, and one name that's constantly tied to these feats is `John Carmack`_, cofounder of id software and pioneer of 3D computer games. His use of ray casting for Wolfenstein 3D and the `fast inverse square root algorithm`_ alone are topics worthy of their own posts, but today I'm going to focus on the algorithm he used to enable real-time 3D level rendering in the original Doom: binary space partitioning (BSP).

Carmack's vision for Doom was to have maps with varying heights, zone-specific lighting, and non-orthogonal walls. Unfortunately, the ray casting algorithm used in id's previous game, Wolfenstein 3D, couldn't render such complex scenes, so he was left looking for a new solution. David Kushner's `Masters of Doom`_, as well as this post on twobithistory_ have already covered this story wonderfully, so I won't go into excessive detail but instead focus on the solution. By representing levels as binary trees of line segments, the rendering engine could quickly decide which surfaces to draw and in what order. Despite being incredibly curious when I first read Masters of Doom, I wasn't working on anything related to computer graphics at the time, and filed BSP trees off for something to look at another day. 

Fast forward to now: I'm trying to incorporate OpenGL rendering into my `ray tracer`_, which requires `constructive solid geometry`_ performed on polygonal meshes. Turns out binary space partitioning is a core part of this algorithm too, so it's finally time to dive in and learn how to create and use BSP trees!

.. _`ray tracer`: https://github.com/rfrazier716/PyRayT
.. _twobithistory: https://twobithistory.org/2019/11/06/doom-bsp.html
.. _`constructive solid geometry`: /posts/efficient-csg/
.. _`Masters of Doom`: http://www.davidkushner.com/book/masters-of-doom/
.. _`metro train in Fall Out 3`: https://www.pcgamer.com/heres-whats-happening-inside-fallout-3s-metro-train/
.. _`spell casting bunnies`: https://kotaku.com/the-invisible-bunnies-that-power-world-of-warcraft-1791576630
.. _`fast inverse square root algorithm`: https://en.wikipedia.org/wiki/Fast_inverse_square_root
.. _`John Carmack`: https://en.wikipedia.org/wiki/John_Carmack


.. contents:: 
    :class: alert alert-primary ml-0

.. contents:: Quick Links
    :depth: 2
    :class: alert alert-primary ml-0

What's So Special About Binary Space?
======================================

Binary space partitioning divides an n-dimensional space into segments that are entirely in front or behind a dividing hyperplane_. For now we'll focus on the 2D case, which means the partition splits a group of line segments into sets that are either in front, behind, or colinear to a dividing line. Repeatedly performing this partitioning on the resulting sets creates a binary tree, where every node contains a dividing line and all colinear segments, and each edge connects to a child node whose segments are completely in front or behind the current node.  

.. _hyperplane: https://en.wikipedia.org/wiki/Hyperplane

.. figure:: /images/bsp_2d/tree_construction.gif
    :align: center
    :width: 600
    
    Construction of a bsp tree by repeatedly subdividing a collection of surfaces. edges labeled + are in front of the previous node, and - are behind.

The most popular use for BSP trees is solving the `which surface problem`_ in computer graphics, notably for the `painter's algorithm`_. As the painter's algorithm draws the entire set of surfaces from back to front, it needs to be able to quickly sort the surfaces from any viewpoint. BSP trees allow for the computationally expensive sorting to happen just once. When the scene needs to be rendered the tree is traveresed in linear time from the current viewpoint and a sorted list of surfaces is generated. It's worth noting this only works for static surfaces, which made it ideal for rendering Doom's level maps. As soon as an individual surface is transformed, however, the entire tree needs to be regenerated. 

.. _`which surface problem`: https://en.wikipedia.org/wiki/Hidden-surface_determination
.. _`painter's algorithm`: https://en.wikipedia.org/wiki/Painter%27s_algorithm

A less famous use of BSP trees is performing constructive solid geometry operations on discrete polygonal meshes. This application uses two separate BSP trees, one for each object the operations are being applied to. the trees are then 'projected' onto each other, resulting in a set of surfaces from one object that are entirely in the other. depending on the operation (union, intersection, or difference), certain surfaces are discarded, and the remaining ones make up the new shape. The actual CSG algorithm is beyond the scope of this post, but the documentation and code for the `csg.js`_ library provides a basic explanation. 

.. _`csg.js`: http://evanw.github.io/csg.js/docs/


Creating a BSP Tree
=============================

Setting up the Environment
---------------------------

In addition to the standard library, we'll use Numpy_ to calculate the line-segment intersections, and NetworkX_ to create the tree. NetworkX is a general purpose graph library that prevents us from having to define our own nodes and edges, and includes extensive traversal algorithms and visualization features. Both packages are installable via pip.


.. _Numpy: https://numpy.org
.. _NetworkX: https://networkx.org

.. code:: shell

    py -m pip install numpy, networkx

The BSP algorithm
------------------

Below are the steps we'll be implementing to create our tree. Given a set of 2D line segments and a dividing line:

1. Calculate the intersection of the dividing line with all segments .
2. Split any segments that intersect the dividing line into two segments at the intersection.
3. Add colinear line segments to the current node of the tree.
4. Create a new child node and repeat steps 1-6 for all segments in front of the dividing line..
5. Create a new child node and repeat steps 1-6 for all segments behind the dividing line
6. Connect the new nodes to the current node with an edge.

Since tree generation is a recursive process, steps 4 and 5 repeat every step up to and *including* themselves until every line segment can be described as colinear to a node. Also, the number of segments in the returned tree may drastically exceed the number of segments in the original set, depending on how many are bisected at each iteration. We'll break the algorithm down into two pieces: the code used to intersect and split a set of segments with a dividing line, and the recursive function that builds the tree.

Bisecting a Line
-----------------

The bulk of the processing is determining where each line segment in a set intersects the dividing line. We'll make a function called :code:`bisect` that accepts an array of line segments and a dividing line, and returns three arrays, one each for segments ahead, behind, and colinear to the dividing line.

.. code:: python

    def bisect(segments: np.ndarray, line: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        # separates a set of line segments based on where they intercept a dividing line

The segments array is an Nx2x2 array, where N is the number of segments being sorted. Each row of the array is a set of two xy-pairs representing the start and endpoints of the segment. For example, a square centered at the origin is composed of four segments:

.. code:: python

    square = np.ndarray([
        [[1,-1],[-1,-1]],
        [[-1,-1],[-1,1]],
        [[-1,1],[1,1]], 
        [[1,1],[1,-1]]
    ])

Similarly, a line is represented by a single 2x2 array of two XY-pairs. The advantage of using Numpy data structures instead of Python lists and tuples is that we can apply the intersection algorithm to the entire segment array at once, instead of iterating over each segment with a for loop. Since Numpy calls compiled C-code, there is almost always a performance gain when a for loop can be replaced with array operators.

The last decision we need to make before writing the bisect function is come up with a consistent definition for what "in front" and "behind" mean in the context of our lines. An easy enough way to visualize it is this: If you take your right hand and orient it so that the pad of your hand is on top of the first point of the line, and your fingers point towards the second, everything on the left side of your hand (closest to the palm) is in front of the line, and everything on the right side (closes to the back of your hand) is behind the line. Later we'll define this more formally with projections onto a normal vector of the line. If the concept of a vector projection is new, I recommend reading up on dot and cross-products, or skipping straight to the implementation_.

.. image:: /images/bsp_2d/line_ahead_behind.png 
    :class: blog-figure
    :align: center

Intersecting Two Lines
```````````````````````

To calculate the intercepts we'll describe the lines and segments as vectors with one independent variable.

.. math::
    \begin{aligned}
    \vec{l}(t) &= \vec{p}_0+(\vec{p}_1-\vec{p}_0)*t \\
    &= \vec{p}_0 + \vec{v}*t
    \end{aligned}

Since segments have a defined start and end, t is valid over a closed range :math:`t \in [0,1]`. Lines on the other hand extend infinitely in all directions, so t can be any real number. For convenience I'm going to refer to our line segments as :math:`\vec{g}(t) = \vec{p_0} + \vec{v}_0t`, and the dividing line as :math:`l(s) = \vec{p}_1 + \vec{v}_1 s`. We're interested in the value :math:`t` where the two lines meet.

.. container:: row

    .. container:: col-lg-5 col-md-12 my-auto

        .. math::
            \begin{aligned}
            \vec{g}(t) &= \vec{l}(s) \\
            \vec{p}_0 + \vec{v}_0 t &= \vec{p}_1 + \vec{v}_1 s \\
            &...
            \end{aligned}\\
            t = \frac{(\vec{p}_1-\vec{p}_0) \times \vec{v}_1}{\vec{v}_0 \times \vec{v}_1}

    .. container:: col-lg-7 col-md-12 my-auto

            .. figure:: /images/bsp_2d/line_intersection.png
                :align: center

                intersection point shown in red

I've skipped a few steps in the above equation because the `intercept of two vector equations`_ is well understood. What we're more interested in is using the results to determine where the segments lie with respect to our line.

Red flags might be going off because this equation is dividing two vectors, which is (1) an invalid operation and (2) can't result in a scaler. Since our lines and segments are all 2D, however, we're going to use the 2D definition of cross product: :math:`\vec{A} \times \vec{B} = A_x*B_y-A_y*B_x`. This scaler is the z-component of the cross product vector we *would* have gotten had we taken a traditional 3D cross-product and set the z-values to zero for :math:`\vec{A}` & :math:`\vec{B}`. 

.. _`intercept of two vector equations`: https://stackoverflow.com/questions/563198/how-do-you-detect-where-two-line-segments-intersect

Ahead, Behind, Bisected or Colinear
``````````````````````````````````````

It's easy to tell that the line bisects a given segment when the t is between 0 and 1. What about the other cases though: how do we determine if the segment is in front or behind the line, and what about cases where t is undefined? To get more insight into what's happening with the intersection equation, we'll look at the numerator and denominator separately.

Numerator
    We already defined the two-dimensional vector cross product: :math:`\vec{A} \times \vec{B} = A_x*B_y-A_y*B_x`. Taking a closer look, it's identical to :math:`(A_x, A_y) \cdot (B_y, -B_x)`, and :math:`(B_y, -B_x)` is the same as rotating :math:`(B_x,B_y)` clockwise 90 degrees, aka it's *proportional to the unit normal vector of the dividing line*. The numerator can be rewritten as:

    .. math::

        ((\vec{p}_0-\vec{p}_1) \cdot \hat{n})|\vec{v}_1|


    Meaning the numerator is taking the distance between two a point on the segment and a point on the line, and projecting that vector onto the normal vector of the line (this is identical to calculating the `shortest distance between a point and a line`_). From our definition of "in front" and "behind", we can claim that a line segment is *partially* in front of the line if the numerator is > 0, and *partially* behind if the numerator is < 0. If the numerator is equal to zero, it means the first point of the segment is on the line, and we need to look at the denominator to define whether it's in front or behind.

.. _`shortest distance between a point and a line`: https://en.wikipedia.org/wiki/Distance_from_a_point_to_a_line

Denominator
    Using the same logic as above, the denominator can be rewritten as a vector projection onto the normal vector:

    .. math::

        -(\vec{v}_0 \cdot \hat{n})|\vec{v}_1|

    This projection is a measure of how far :math:`\vec{g}(t)` travels towards line :math:`\vec{l}(s)` per interval t. Since the numerator is how far the lines are apart (projected onto the normal vector), and the denominator is how fast one line is approaching the second along that same normal, it makes sense that the ratio is the amount of time (t) until they intersect!
    
    If the denominator is equal to zero, the two lines are parallel, and the sign of the numerator determines where the segment lies relative to the line. 

With the exception of cases where t is between 0 & 1, the numerator and denominator must be considered when defining the segments location. A summary of all cases is given below.


.. class:: table table-striped table-sm blog-table bsp-cases w-85 mx-auto 

+----------------+-----------+-------------+-----------------------+
|       t        | Numerator | Denominator | Line Segment Location |
+================+===========+=============+=======================+
| 0 < t < 1      | \-        | \-          | Bisected by line      |
+----------------+-----------+-------------+-----------------------+
| t > 0 or t < 1 | > 0       | \-          | In front of line      |
+----------------+-----------+-------------+-----------------------+
| t > 0 or t < 1 | <0        | \-          | Behind line           |
+----------------+-----------+-------------+-----------------------+
| t = 0          | \-        | < 0         | In front of line      |
+----------------+-----------+-------------+-----------------------+
| t = 0          | \-        | > 0         | Behind line           |
+----------------+-----------+-------------+-----------------------+
| \-             | = 0       | = 0         | Colinear              |
+----------------+-----------+-------------+-----------------------+

.. _implementation: 

Putting it Into a Function
``````````````````````````````````````
Cases in hand we're ready to implement the first half of our bisect function! 

.. include:: files/bsp_2d/bisect_stub.py
    :code: python

Right now all it does is build a set of boolean masks used to index the segment array. Before returning the new segments we need to write some code to split bisected segments into two new segments. Notice how when calculating t the denominator has an extra component :code:`parallel`. This boolean value is cast as a 1 if the denominator would have been zero, and prevents Numpy from throwing a warning about divide by zero errors.

Handling Bisected Lines
````````````````````````

If a segment is bisected by the line at time t, we need to create two new segments, one from 0-t, and a second from t-1. Fancy indexing with Numpy can be slower than doing simple operations on an entire array (this is highly dependent on the application), so we'll create two new segments for every segment and then filter.

.. code:: python

    intersection_points = segment_start + intersection[..., np.newaxis] * v0
    l_segments = np.stack((segments[..., 0, :], intersection_points), axis=1)
    r_segments = np.stack((intersection_points, segments[..., 1, :]), axis=1)

Notice how they're split into left and right segments, not 'in front' and 'behind'. That's because right now we don't know which segments are which, and need to filter them based on the numerator. If the numerator is >0, the first point of the segment is ahead of the line, making :code:`l_segment` ahead and :code:`r_segment` behind. 

.. code:: python

    mask = numerator[..., np.newaxis, np.newaxis] > 0
    bisected_ahead = np.where(mask, l_segments, r_segments)[bisected]
    bisected_behind = np.where(np.logical_not(mask), l_segments, r_segments)[bisected]

.. figure:: /images/bsp_2d/left_right_segments.png
    :align: center

    An example of two segments where the left and right splits are on opposite sides of the dividing line


Once the bisected segments have been split, all that's left to do is combine them with their respective ahead/behind sets, and return the three sets of segments. The full function is found here_, with a set of if statements to catch cases where ahead/behind sets are empty arrays. The :code:`Tuple` Typehint is from the typing_ module, and is useful for IDE's to infer what types the function will return.

.. _typing: https://docs.python.org/3/library/typing.html
.. _here: https://github.com/rfrazier716/bsp/blob/12af4fba95cc594b2f3da604491de75d508d1d58/bsp.py#L9

Recursively Building the Tree
--------------------------------

Compared to the amount of code required to partition our line segments, the function build the BSP tree is relatively simple.

.. include:: files/bsp_2d/build_tree.py
    :code: python

Let's pick it apart, starting with the function signature. The function expects a nx2x2 array of line segments, and an optional starting segment that it used as the first dividing line. The output will be a NetworkX directed graph object where every node is a dividing line holding the colinear segments for that line.

.. code:: python

    def build_tree(segments: np.ndarray, starting_segment: np.ndarray = None) -> nx.DiGraph:

Next is the initialization block, here we create the actual graph object and check if the user provided a starting segment. If no segment was given, the first segment of the array is used instead. The function then calls the bsp_helper function that fills the graph with divided segments, and then relabels all nodes sequentially before returning the graph.

.. code:: python

    graph = nx.DiGraph()  # make a new directed graph
    if starting_segment is None:
        starting_segment = segments[0]

    # run the recursive helper function, which should add all nodes and edges
    bsp_helper(segments, starting_segment)
    return nx.relabel.convert_node_labels_to_integers(graph)

The final piece is the nested bsp_helper function. Defining bsp_helper within build_tree allows it to access the graph variable without explicitly passing it (this is part of the `enclosing scope`_ in an LEBG model). It also keeps bsp_helper out of the module namespace. The function calculates where each segment in a set falls relative to the dividing line. It then creates a new node with two attributes: the dividing line of the node, and any segments that are colinear to that dividing line. If there's any segments in front of the line, the helper function recursively calls itself with only the set of segments ahead of current dividing line, returning the id of the created node. The returned node is connected to the current node with an edge, whose position attribute is +1 (meaning it's ahead of the current node). The same is then done for segments behind the current line. If recursive functions are a new concept, RealPython has a `great tutorial`_ on understanding and implementing them, as well as introduces the `@lru_cache`_ decorator.

.. _`enclosing scope`: https://realpython.com/python-namespaces-scope/#variable-scope
.. _`great tutorial`: https://realpython.com/python-thinking-recursively/
.. _`@lru_cache`: https://docs.python.org/3/library/functools.html#functools.lru_cache 


Taking it for a Test Drive
===========================

As a last step we'll create a tree from scratch and plot the results. First lets make a function to draw the segments stored in a BSP tree, with markers showing where the the segments are divided. The drawing itself will be handled by matplotlib_, which can also be installed from pip.

.. _matplotlib: https://matplotlib.org

.. code:: python

    def draw_segments(tree: nx.DiGraph, axis=None, *args, **kwargs) -> None:
        if axis is None:
            axis = plt.gca()
        all_segments = np.concatenate([value for value in dict(nx.get_node_attributes(tree, "colinear_segments")).values()])
        for segment in all_segments:
            axis.plot(*(segment.T), *args, **kwargs)

Next we'll import some `prebuilt line segments`_ and reshape the list of points into an appropriate shape. Then it's as simple as creating the bsp tree and plotting the results!

.. _`prebuilt line segments`: /bsp_2d/points.csv

.. code:: python

    segments = np.loadtxt("points.csv")
    segments = segments.reshape(int(segments.shape[0] / 4), 2, 2)

    tree = build_tree(segments)
    fig = plt.figure()
    draw_segments(tree, color='k', marker='o')
    plt.show()

.. figure:: /images/bsp_2d/doom_tree.png
    :align: center
    :width: 800

    The fruit of our labor, bisected points are shown in red

Despite creating an impressive BSP tree, at the end of the day it's still just a graph, and could use a killer application to make the power of BSP shine! `The full code`_ has additional functions for performing operations on trees as well as implementing CSG operations. Alternatively, pair BSP with Pyglet_ you're half way towards a working 2.5D game engine.  

.. _`pyglet`: http://pyglet.org
.. _`The full code`: https://github.com/rfrazier716/bsp/blob/master/bsp.py




