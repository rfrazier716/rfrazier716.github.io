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

Extending for an Arbitrary number of Surface Intersections
===========================================================

Unfortunately, the above logic falls apart as soon as any surface returns more than two intersections. In the circle case above if they ray went through the top of the circles instead of the middle, it would need to return four hits instead of just two. Additionally there would be no overlap between the hit vectors of the two circles. Now imagine a case where you want to combine two general surfaces, who themselves are the results of many CSG operations. If we applied the logic above, each hit array would need to be broken into discrete pairs and compared to the other shapes pairs, an expensive operation that does not scale well as the number of hits grows. 

Before writing the general algorithm, we're going to make some assumptions about our hits vectors and the surfaces being operated on:

Both surfaces are closed surfaces
    write note

Each hit array has an even number of elements
    write note

The hit arrays are sorted
    write note

Odd indexed hits enter the surface, even valued hits leave the surface
    write note



.. class:: alert alert-primary
    TODO: put a picture of the wavedrom trace with A, B and then A+B, A-B, A&B, and a count of how many surfaces are interacted



> Put gherkin test case here

Creating a surface count vector
----------------------------------

The first step is to generate the surface count vector, so that we can track if the ray is inside one, both, or neither surfaces. 

#. Make a new array of hits that is the concatenation of both hit arrays
#. Make a second array of alternating +/-1 the length of the concatenated array.
#. Sort both arrays by the concatenated hits array
#. Take the cumulative sum of the +/-1 array.

The +/-1 in the second array is being used as an indicator for if a hit is entering or exiting one of the two surfaces, since both arrays have an even number of elements and (as mentioned above) every odd value in a hit array must enter a surface, and every even hit must exit, the array can be quickly constructed with alternating values. After sorting both arrays by the concatenated hits array, the count array still represents when the rays enter and exit a surface, but now it's sorted by time. Finally, the accumulated count array recreates our surface count vector, tracking how many surfaces the ray is currently in.


.. class:: alert alert-primary

    TODO: put a picture in of the accumulation steps/a code example

Using the surface count vector we can now handle the boolean union and difference operations

The Union Operator
-------------------

Take a look at the union operator and corresponding count values. Notice that union hits are any any index (n) where count[n-1]==0 and count[n]==1, or count[n-1]==1 and count[n]==0. This is the same as taking the exclusive or (XOR) of the array with a copy of itself shifted down by one row. From above we know that the last value of the count array has to be 0 (at :math:`t=\inf` the ray must have exited all surfaces), so the shifted array will always have be all zeros in the zeroth row. Numpy gives us all the function calls needed to efficiently perform xor on our count array, shown below. 

.. code:: python

    def csg_union(hit_array: np.ndarray, count_array:  np.ndarray) -> np.ndarray:
        mask = np.logical_xor(count_array, np.roll(count_array, 1 axis=0))
        csg_hits = np.where(mask, hit_array, np.inf)
        return csg_hits

A couple things from this code might pop out: (1) why specify the axis when rolling a 1D array, and (2) why does csg_hits need the same dimension as hit_array, padded with np.inf, instead of just returning the valid hits. Both of these are addressed in **PUT THE SECTION HEADER HERE**. 

* put a comment here about plugging it into test cases and check that it's passing *

The Intersection Operator
--------------------------

The intersection operator can be handled in a similar manner. Looking at the count array, an intersection hit occurs at any index (n) where count[n] == 2 or count[n-1] == 2. This time we'll use numpy's :code:`logical_or` function to create the mask

.. code:: python

    def csg_intersection(hit_array: np.ndarray, count_array:  np.ndarray) -> np.ndarray:
        is_two = np.where(count_array==2)
        mask = np.logical_or(is_two, np.roll(is_two, 1 axis=0))
        csg_hits = np.where(mask, hit_array, np.inf)
        return csg_hits

Again it's important to make sure the function tests pass before continuing. 

The Difference Operator
------------------------

The difference operator is unique from the union and intersection operator. Both union and intersection have analogs in boolean algebra, where a union is defined as :code:`A|B` and in intersection is :code:`A & B`. Boolean algebra, however, does not have the concept of subtraction. Not only that, but we can't use the clever tricks from the count array, since we need to know which surface is the subtracting surface, and the count array only tracks how many closed surfaces the ray is inside. Instead of coming up with an entirely new method just for differences, we're going to redefine what a difference means to it fits with the existing functions. Instead of thinking of A-B as shape B cutting away from shape A, think of it as the intersection of A with the infinitely large volume of space where B *does not* exist, called :math:`\bar{B}`. 

.. class:: alert alert-primary

    TODO: put a 2d example of boolean subtraction and intersection with negative space

Defining the function in this way lets us reuse the the same principle as the intersection operator, but first the count array has to be redefined for an inverted shape. An inverted shape still has to follow the assumptions from above, but instead of the ray entering and exiting the shape at the first and last hit, it enters the shape at :math:`-\infty` and *exits* the shape at the first hit in the hit array. Similarly, the ray *enters* the shape at the last hit of the hit array, and exits at :math:`\infty`. Instead of padding the array with :math:`+/-\infty` and sorting, the following observations will make it so we don't have to resize the array.

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

The Full Function 
==================

** Do something here about passing test cases**

Extending for 2D Matrices
==========================

Potential Speed ups
--------------------

