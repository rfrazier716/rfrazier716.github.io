.. title: Rendering Constructive Solid Geometry With Python
.. slug: efficient-csg
.. date: 2021-03-15 07:35:26 UTC-04:00
.. tags: ray tracing, python, csg, constructive solid geometry, rendering, numpy, pyrayt
.. category: Programming
.. link: 
.. description: 
.. type: text
.. has_math: true
.. status: published

.. role:: py(code)
   :language: python

I recently hit a road block with my `ray tracer`_: cubes, cylinders, and spheres rendered fine, but there wasn't an easy way to create arbitrary shapes whose intersection and normal functions I hadn't already hard coded. Since PyRayT's end use is for optical design, at the bare minimum it needed a flexible way to create lenses and mirrors. Flipping through Jamis Bucks' `The Ray Tracer Challenge`_, it turns out the last chapter *Constructive Solid Geometry* (CSG) addressed my needs perfectly! However, Buck's equations for CSG did not blend well with PyRayTs flow of rendering multiple rays at once. Today I'll be covering my own algorithm for adding constructive solid geometry to a ray tracer, as well as its implementation in Python using numpy_.

.. _`The Ray Tracer Challenge`: https://pragprog.com/titles/jbtracer/the-ray-tracer-challenge/
.. _`ray tracer`: https://github.com/rfrazier716/PyRayT
.. _numpy: https://numpy.org

.. TEASER_END

.. contents::
    :class: alert alert-primary col-md-4


CSG In a Nutshell
==================

An easy way to create complex surfaces from basic shapes, constructive solid geometry is based around three fundamental operations: union, intersect, and difference. Each operation acts on two shapes, resulting in a new shape that is a combination of the two. multiple CSG operations can be chained together, creating increasingly intricate shapes while using significantly less surfaces than an equivalent triangular mesh. 

.. figure:: /images/efficient_csg/csg_operations.png
    :align: center
    :width: 800

    The three base operations for Constructive Solid Geometry. **Union (∪)** combines both shapes, **intersection (∩)** returns only the common volume of both spaces, and **difference (-)** subtracts the second shape from the first.

What It Means for Ray Tracing
------------------------------

Ray tracing with CSG's is surprisingly straightforward. When a ray is interesected with a CSG object, it is really intersected with the set of surfaces that make up the object. The job of the CSG algorithm is to take those two sets of intersections and filter them out so that only valid ones remain. These hits are then returned to the renderer so it can determine the closest surface that the ray interacts with.

.. figure:: /images/efficient_csg/example_hits.png
    :align: center
    :width: 600

    An example of rendering the union of two surfaces. While each sub-shape returns a full set of intersections, the filter function discards points a1 and b0 since they are inside of the new object. 

Writing a function to sort valid CSG hits turns out to be nontrivial. for every ray-surface hit, the function needs to determine if the hit occurred inside the opposite surface. This is easy enough for convex surfaces that have at most two intersections per ray, but as the number of intersections grows, basic methods for checking fall apart or slow down significantly.

.. figure:: /images/efficient_csg/csg_timeline.png
    :align: center
    :width: 500

    Complex hit arrays for two surfaces A & B, and the expected hit arrays for CSG Operations on those surfaces. 


Writing a Function to Filter Hits
==================================

Every method I found to filter out csg intersections involved iterating over all hits in a set, and internally keeping track of two booleans that determine if the ray is inside of each surface at a given hit. By contrast, this approach operates on the entire array at once, but leverages a couple assumptions about the surfaces being intersected:

Both surfaces are closed surfaces
    *"A closed surface is a surface that is compact and without boundary."* While this definition is accurate, it's not exactly intuitive to imagine what surfaces are closed and which are open. I visualize closed surfaces as "if I were to look at this surface from any angle, can I tell if it's hollow without cutting it open". If the answer is no, it's closed, otherwise it's an open surface with a boundary.

    By asserting that all surfaces are closed surfaces, you can also claim that **each hit array has an even number of elements**. Since Rays extend from time :math:`-\infty` of :math:`\infty`, any ray that enters a surface *must* exit the surface. Even if the surface has infinite volume, the ray will then enter and exit at :math:`\mp\infty`. 
    
    Additionally, CSG becomes meaningless if the surfaces are not closed. Imagine subtracting an infinitely thin plane from a sphere. Since planes have no depth you don't remove any material from the sphere, and end up with the same shape you started with!

The hit arrays are sorted
    We'll use the position of intersections in their respective arrays to determine if the ray is entering or exiting the surface. In order for it to work, both input arrays must be sorted.

Odd indexed hits enter the surface, even valued hits leave the surface
    Since the intersection arrays are sorted, and include all hits from :math:`-\infty` to :math:`\infty`, the first element each hit array *must* be the ray entering the respective surface. It's also impossible for the ray to enter the surface again without first leaving it. so the next hit represents the ray leaving the surface. This alternating pattern continues for the entire hit array.

The surface_count vector
----------------------------------

There's two additional arrays we'll use validate hits: a sorted array of all hits for both surfaces, and an array that tracks how many surfaces the ray is inside of at each hit, called surface_count.

.. figure:: /images/efficient_csg/surface_count.png
    :align: center
    :width: 500

    The same intersection arrays from above and the corresponding surface_count array

To create surface_count we'll do the following

#. Create a concatenated array of both hit arrays (but do not sort it yet)
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

Union
------

.. image:: /images/efficient_csg/union_count.png
    :align: center
    :width: 500

Take a look at the union operator and corresponding count values. Notice that union hits are any any index (n) where count[n-1]==0 and count[n]==1, or count[n-1]==1 and count[n]==0. This is the same as taking the exclusive or (XOR) of the array with a copy of itself shifted down by one row. From above we know that the last value of the count array has to be 0 (at :math:`t=\infty` the ray must have exited all surfaces), so the shifted array will always have be all zeros in the zeroth row. Numpy gives us all the function calls needed to efficiently perform xor on our count array, shown below. 

.. code:: python

    surface_count = np.logical_xor(surface_count, np.roll(surface_count,1,axis=0))
    csg_hits = np.where(surface_count != 0, merged_array, np.inf)

A couple things from this code might pop out: (1) why specify the axis when rolling a 1D array, and (2) why does csg_hits need the same dimension as hit_array, padded with np.inf, instead of just returning the valid hits. Both of these are addressed in `Extending To 2D Matrices`_. 

Intersection
-------------

.. image:: /images/efficient_csg/intersection_count.png
    :align: center
    :width: 500

The intersection operator can be handled in a similar manner. Looking at the count array, an intersection hit occurs at any index (n) where count[n] == 2 or count[n-1] == 2. This time we'll use numpy's :code:`logical_or` function to create the mask

.. code:: python

    is_two = (surface_count == 2)
    mask = np.logical_or(is_two, np.roll(is_two, 1, axis=0))
    csg_hits = np.where(mask, merged_array, np.inf)

The intersection operator has an interesting "blip" at t=5. This is because both surfaces have a hit at 5, but in one case the ray is entering the surface, and the other it is exiting. With integer math this becomes a 'zero thickness' shell, but it can cause unintended results when the hits are floating-points and the surfaces overlap by a small amount. 

Difference
-----------

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

Here the xor operator is inverting the array mask for any indices in the argsort that reference the right_array.


.. _`Extending To 2D Matrices`:

Extending To 2D Matrices
-------------------------

PyRayT can perform reasonably fast ray tracing because under the hood every ray is stored in a 2x4xn matrix that gets intersected with each surface. This allows me to bypass Python for loops in favor of heavily optimized numpy functions. Fortunately, by specifying axes and preserving array sizes, the csg function can be readily extended to 2D matrices, where every column represents the ordered hits for an individual ray with the given surface.

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

Before passing this function off as complete, we need to make sure it passes some basic unit tests. I'll be using Python's UnitTest framework to make sure that the two hit arrays plotted above return the correct values for union, intersection, and difference.

.. include:: files/efficient_csg/test_cases.py
    :code: python

With those tests passing, we're one step closer to a fully fledged Python ray tracer!

Conclusion
===========

.. raw:: html

    <div class="container">
        <div class="row">
            <div class="col-md-8 my-auto">
            <p>
                Constructive Solid Geometry can extend the functionality of a ray tracer by building complex shapes from basic primitives, but rendering them requires an additional step to filter out which intersections are valid. Thanks to numpy, it's easy to write this function without reverting to Python for loops, and the same function can be used to process multiple ray-surface intersections at once.
            </p>
            <p>
                In PyRayT, all lenses are CSG intersections of two spheres (defining the focus) and a cylinder that sets the aperture. This has sped up development time and is significantly easier than writing custom functions for each optical component.
            </div>
            <div class="col-md-4">
                <img src="/images/efficient_csg/csg_in_action.png" alt="a cool looking, albeit meaningless example of CSG in action">
            </div>
        </div>
    </div>

.. class:: alert alert-primary

    You may have noticed the shading in these CSG surfaces seems a bit *off*. They're rendered with what's called a `Gooch shader`_, which is specifically designed to be non-photorealistic. In my next post I'll discuss adding Gooch shading to PyRayT, and it's tradeoffs compared to other shader models.

.. _`Gooch shader`: https://en.wikipedia.org/wiki/Gooch_shading


