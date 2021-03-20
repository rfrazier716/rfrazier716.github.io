.. title: Efficient CSG
.. slug: efficient-csg
.. date: 2021-03-15 07:35:26 UTC-04:00
.. tags: 
.. category: 
.. link: 
.. description: 
.. type: text
.. has_math: true

.. role:: py(code)
   :language: python

I recently hit a road block with my ray tracer: cubes, cylinders, and spheres rendered fine, but there wasn't an easy way to create arbitrary shapes whose intersection and normal functions I hadn't already hard coded. Since PyRayT's end use is for optical design, at the bare minimum it needed a flexible way to create lenses and mirrors. Flipping through Jamis Bucks' "The Ray Tracer Challenge", it turns out the last chapter "Constructive Solid Geometry" (CSG) addresses my needs perfectly! However, Buck's equations for CSG were unnecessarily complicated, and would slow down PyRayT excessively. In this post I'll be covering my algorithm for implementing constructive solid geometry in a ray tracer, as well as it implementation in Python using numpy.

.. contents::
    :class: alert alert-primary col-md-4


CSG In a Nutshell
==================

An easy way to create complex surfaces from basic shapes, constructive solid geometry is based around three fundamental operations: union, intersect, and difference. Each operation acts on two shapes, resulting in a new shape that is a combination of the two. multiple csg operations can be chained together, creating increasingly intricate shapes while using significantly less surfaces than an equivalent triangular mesh. 

Union
    definition

Intersection 
    definition

Difference
    Definition

What It Means for Ray Tracing
------------------------------

Ray tracing with CSG's is surprisingly straightforward. When you render a scene with a CSG object in it, the ray is intersected with each sub-surface that makes up the object, returning a full set of 'hit' points that need to be filtered. The CSG object then needs to look at both sets of hits and decide which ones are valid for the boolean operation being performed on the surfaces. These hits are then returned to the renderer so it can determine the closest surface that the ray interacts with.

.. figure:: /images/efficient_csg/csg_timeline.png
    :align: center
    :width: 500

despite the ray tracing being straightforward, writing a function to sort valid CSG hits turns out to be more complex. for every ray-surface hit, the function needs to determine if the hit occurred inside the opposite surface. This is easy enough for convex surfaces that have at most two intersections per ray, but as the surfaces become more complex basic methods for checking intersections overlap. 

Below is a simplified snapshot of the `intersect` function for CSGObjects in PyRayT, showing where the sorting function is called

.. code:: python

    def intersect(self, rays):
        l_hits = self._l_child.intersect(rays)
        r_hits = self._r_child.intersect(rays)

        # this is the function we'll be implementing
        csg_hits = array_csg(l_hits, r_hits, self._operation)

        return csg_hits


A Scalable Algorithm to Filter Hits
===========================================================

Brushing up on the Fundamentals 
--------------------------------

Before writing the general algorithm, I'm going to make some assertions about the hits vectors and the surfaces being operated on:

Both surfaces are closed surfaces
    *"A closed surface is a surface that is compact and without boundary."* While this definition is accurate, it's not exactly intuitive to imagine what surfaces are closed and which are open. I visualize closed surfaces as "if I were to look at this surface from any angle, can I tell if it's hollow without cutting it open". If the answer is no, it's closed, otherwise it's an open surface with a boundary.

    .. image:: /images/efficient_csg/solid_bodies_crop.png
        :align: center
        :width: 500

    By asserting that all surfaces are closed surfaces, you can also claim that **each hit array has an even number of elements**. Since Rays extend from time :math:`-\infty` of :math:`\infty`, any ray that enters a surface *must* exit the surface. Even if the surface has infinite volume, the ray will then enter and exit at :math:`+/-\infty`. 
    
    Additionally, CSG becomes meaningless if the surfaces are not closed. Imagine subtracting an infinitely thin plane from a sphere. Since planes have no depth you don't remove any material from the sphere, and end up with the same shape you started with!

The hit arrays are sorted
    Sorts are expensive to perform on large arrays, and I want PyRayT to be as fast as possible (while still being able to leverage Python to quickly develop code). The intersection functions in PyRayT are always set up to return sorted arrays, so this assumption prevents an additional, unnecessary sort. However, *The arrays must be sorted for this algorithm to work.* If your intersections don't return sorted hits, make sure to sort the arrays before passing them.

Odd indexed hits enter the surface, even valued hits leave the surface
    Since we know that the hit arrays are sorted, and that rays extend to infinity, the first element each hit array *must* be the ray entering the respective surface. It's also impossible for the ray to enter the surface again without first leaving it. so the next hit represents the ray leaving the surface. This alternating pattern continues for the entire hit array.

The surface_count vector
----------------------------------

We'll create two additional arrays to help validate hits: a sorted array of all hits for both surfaces, and an array that tracks how many surfaces the ray is inside of at each hit, called :code:`surface_count`.

.. image:: /images/efficient_csg/surface_count.png
    :align: center
    :width: 500

To create surface_count we'll do the following

#. Create a concatenated array of both hit arrays (But do not sort it yet)
#. Take the argsort of the concatenated array
#. create a new array with the same dimension as the concatenated array. For each index in the new array, assign +1 if the value in the equivalent argsort index is even, and -1 if is odd
#. take the cumulative sum of the +/-1 array, this is the surface count array.
#. sort the concatenated hit array

The +/-1 array is being used as an indicator for if a hit is entering or exiting one of the two surfaces. Since both arrays have an even number of elements, every odd value of the concatenated array must enter a surface, and every even hit must exit. numpy's :code:`where`, combined with argsort and cumsum are all we need to create surface_count. Once we have that we're ready to tackle the first of our Boolean operators.

.. code:: python

    merged_array = np.concatenate((array1, array2))
    merged_argsort = np.argsort(merged_array, axis=0)
    merged_array = merged_array[merged_argsort]
    merged_mask = np.where(merged_argsort & 1, -1, 1)
    surface_count = np.cumsum(merged_mask, axis=0)


The Union Operator
-------------------

Take a look at the union operator and corresponding count values. Notice that union hits are any any index (n) where count[n-1]==0 and count[n]==1, or count[n-1]==1 and count[n]==0. This is the same as taking the exclusive or (XOR) of the array with a copy of itself shifted down by one row. From above we know that the last value of the count array has to be 0 (at :math:`t=\infty` the ray must have exited all surfaces), so the shifted array will always have be all zeros in the zeroth row. Numpy gives us all the function calls needed to efficiently perform xor on our count array, shown below. 

.. code:: python

    surface_count = np.logical_xor(surface_count, np.roll(surface_count,1,axis=0))
    csg_hits = np.where(surface_count != 0, merged_array, np.inf)

A couple things from this code might pop out: (1) why specify the axis when rolling a 1D array, and (2) why does csg_hits need the same dimension as hit_array, padded with np.inf, instead of just returning the valid hits. Both of these are addressed in `Extending To 2D Matrices`_. 

The Intersection Operator
--------------------------

The intersection operator can be handled in a similar manner. Looking at the count array, an intersection hit occurs at any index (n) where count[n] == 2 or count[n-1] == 2. This time we'll use numpy's :code:`logical_or` function to create the mask

.. code:: python

    is_two = (surface_count == 2)
    mask = np.logical_or(is_two, np.roll(is_two, 1, axis=0))
    csg_hits = np.where(mask, merged_array, np.inf)

Again it's important to make sure the function tests pass before continuing. 

The Difference Operator
------------------------

The difference operator is unique from the union and intersection operator. Both union and intersection have analogs in boolean algebra, (or the binary equivalent *and* and *or* operators). Boolean algebra, however, does not have the concept of subtraction. Not only that, but we can't use the clever tricks from the count array, since we need to know which surface is the subtracting surface, and the count array only tracks how many closed surfaces the ray is inside. Instead of coming up with an entirely new method just for differences, we're going to redefine what a difference means so it it behaves like a boolean operation.

Instead of thinking of A-B as shape B cutting away from shape A, think of it as the intersection of A with the infinitely large volume of space where B *does not* exist, called :math:`\bar{B}`. 

.. image:: /images/efficient_csg/csg_difference.png
    :align: center
    :width: 900

Defining the function in this way lets us reuse the the same principle as the intersection operator, but first the count array has to be redefined for an inverted shape. An inverted shape still has to follow the assumptions from above, but instead of the ray entering and exiting the shape at the first and last hit, it enters the shape at :math:`-\infty` and *exits* the shape at the first hit in the hit array. Similarly, the ray *enters* the shape at the last hit of the hit array, and exits at :math:`\infty`. 

.. image:: /images/efficient_csg/inverted_difference.png
    :align: center
    :width: 500

Instead of padding the array with :math:`+/-\infty` and sorting, the following observations will make it so we don't have to resize the array.

* The hit at :math:`-\infty` will always be the first hit in the sorted hits array, meaning the first value in the cumulative sum will *always* be a 1. This is the same as adding 1 to the count array and ignoring the hit at :math:`-\infty`.

* The hit at :math:`+\infty` will always be the last hit in the sorted hits array. If we ignore it, the cumulative sum's final value will be 1 instead of 0 (since we're still inside of the inverted surface). However, looking at the Intersection operator, we only care about finding indices where count[n]==2, so we're safe to ignore it.

* instead of filling the mask array with alternating +/-1, it needs to be filled with +/-1 from 0:n, where n is the length of the first hit array, and -/+1 from n:-1. This will successfully "invert" the second shape, where hits that used to enter the surface now exit, and visa versa. 

With those observations in hand we're ready to create the count array for the difference operator, and once again numpy's :code:`logical_xor` will simplify the task.

.. code:: python

    merged_array = np.hstack((left_array, right_array))
    merged_argsort = np.argsort(merged_array,axis=0)

    count_array = np.where(np.logical_xor(merged_argsort&1, merged_argsort>=left_array.shape[-1]))
    count_array = np.cumsum(count_array)+1

Here the xor operator is inverting the array mask for any indices in the argsort that reference the right_array. **INCLUDE XOR TRUTH TABLE???**


.. _`Extending To 2D Matrices`:

Extending To 2D Matrices
==========================

PyRayT can perform reasonably fast ray tracing because under the hood every ray is stored in a 2x4xn matrix that gets intersected with each surface. This allows me to bypass python for loops in favor of heavily optimized numpy functions that are calling compiled C and fortran libraries. Fortunately, by specifying axes and preserving array sizes, the csg function can be readily extended to 2D matrices, where every column represents the ordered hits for an individual ray with the given surface.

The only thing we need to change is how the arrays are concatenated. If a 1D array is passed, they can be concatenated along the zero axis, but 2D arrays need to be stacked column-wise

.. code:: python

    if array1.ndim == 1:
        # if 1D arrays were passed, concatenate
        merged_array = np.concatenate((array1, array2))
        merged_argsort = np.argsort(merged_array, axis=0)
        merged_array = merged_array[merged_argsort]

    else:
        # otherwise stack them where each column represents a unique ray's hits
        merged_array = np.vstack((array1, array2))
        merged_argsort = np.argsort(merged_array, axis=0)
        merged_array = merged_array[merged_argsort, np.arange(merged_array.shape[-1])]


The Full Function 
==================

The complete function is shown below. There's an additional helper class `Operation` that inherits from Enum used to select the which CSG operation is performed (I prefer Enums over string arguments for anything end users won't see). Also, there's an optional argument :code:`sort_output` that sets if the returned array is sorted along the hit axis. The reason for this option is to eliminate unnecessary :code:`np.sort()` calls on large arrays that slow down the final program.

.. include:: files/efficient_csg/csg.py
    :code: python

Verifying Test Cases 
---------------------

The last step is to make sure the test cases all pass. I'll be using UnitTest ...

.. include:: files/efficient_csg/test_cases.py
    :code: python

CSG In Action 
==============

