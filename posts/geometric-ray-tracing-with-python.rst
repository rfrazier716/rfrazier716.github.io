.. title: Geometric Ray Tracing with Python
.. slug: geometric-ray-tracing-with-python
.. date: 2021-03-06 16:51:24 UTC-05:00
.. tags: adventures in ray tracing
.. category: Programming
.. link: 
.. description: 
.. type: draft


Ray tracing is subset of programming that has always fascinated me. Every time you see a computer generated image, from video games to CAD software, ray tracing took place under the hood. The biggest hurdle I've always found with learning about ray tracers, though, is it's tightly coupled with graphics API's such as openGL and DirectX, and the actual algorithms are abstracted away from the user.

.. TEASER_END:

In this post, I'll give an overview of what a ray tracer is and where they're used in the real world. I'll cover the base components that make up a ray trace, how a ray trace state-machine is structured, and give implementation examples with Python, showing how a couple linear algebra tricks can speed up your ray trace considerably. At the end I'll highlight next steps, which will be covered in future posts, that will extend the basic example into a fully capable ray tracer.

.. contents::
    :class: alert alert-primary float-md-right

Brush Up on the Basics
=======================

What is a Ray Tracer?
~~~~~~~~~~~~~~~~~~~~~~
Stripped to its core, a ray tracer is nothing more than a geometry solver, whose goal is to find the intersection of a set of rays with surfaces in space. Most often, however, ray tracers are used to simulate light's interaction with real world objects, either for rendering or analytic purposes. Regardless of the final application, all ray tracers rely on two fundamental pieces to function:

Rays
    Rays are used to represent light, and are composed of two vectors: position and direction. Position is the

Surfaces
    Put Definition of a Surface

Ray Tracers in Computer Graphics
---------------------------------

Ray Casting, Ray Tracing, and Path Tracing
```````````````````````````````````````````
ray casting, ray tracing, and path tracing have muddled definitions depending on the sources. Despite having their own unique wikipedia pages, ray casting and tracing are effectively the same thing, with ray casting being used in the context of CAD software and early "3D" videogames, and ray tracing used when describing rendering scenes.

.. class:: alert alert-secondary float-md-center

    Roth invented the term "ray casting" before hearing of “ray tracing”, but they are essentially the same. His development of ray casting at GM Research Labs occurred concurrently with Turner Whitted’s ray tracing work at Bell Labs. - wikipedia_

    .. _wikipedia: https://en.wikipedia.org/wiki/Ray_tracing_(graphics)

In a ray cast/trace, a set of rays is projected from the camera to find the nearest intersected surface. From there additional rays may be generated to calculate lighting, but in some cases it is not necessary.

.. class:: alert alert-primary
    
    TODO: add an image of a shaded sphere and wolfenstein 3D, noting how both use ray tracing at their cores to generate images

Path tracing distinguishes itself from the other two by using random sampling to more accurately recreate the path light takes from a source to the observer. At every ray-surface intersection, one or more child rays are generated from a random distribution based on the material properties of the intersected surface. These child rays in turn propagate through the system to intersect new surfaces. This process is repeated until the rays intersect a light source, and the pixel value is calculated from all the surface intersections in the ray's history. Since a single ray cannot intersect all light sources, multiple rays are are generated for every pixel of the final image, where the final pixel color is the average value of all ray paths. 

The random nature of path tracing makes renders look noisey, or "speckled", if not enough test rays are generated, and take longer to render compared to traditional ray traces. The advantage is a significantly more realistic looking final image, where features like `soft shadows`_, caustics_, and bokah_ naturally form as light explores random paths.

.. _`soft shadows`: https://en.wikipedia.org/wiki/Hard_and_soft_light
.. _caustics: https://en.wikipedia.org/wiki/Caustic_(optics)
.. _bokah: https://en.wikipedia.org/wiki/Bokeh

.. class:: alert alert-primary
    
    TODO: add image of sphere in blender with differnet rays per pixel showing noise


Video Games and Real Time Ray Tracing
``````````````````````````````````````

Ray Tracers in Engineering
---------------------------
In optical design, ray tracers are used to simulate how light propagates through an optical system, such as a camera or microscope. Unlike renderers, the output of engineering ray traces is typically a collection of ray segments, and tracks information such as intensity, which surface was intersected, and optical length. Often rays will have unique IDs so a single ray can be traced through an entire system.

The goal of these types of ray tracers is not to create an image, but instead to provide an accurate model of how light interacts with the environment. So shortcuts and approximations that can be used for rendering are not implemented (e.g. the Phong reflection model).

Limitations
````````````
While the goal of an these ray traces is to create an accurate physical model, limitations arise from the fact that ray tracers ignore the wave nature of light. wave effects: interference, diffraction, polarization etc. can all be added on top of a "geometric" ray trace, but are limited in their applications (you wouldn't use a ray tracer to design a single mode waveguide, for example). When the full wave-nature of light needs to be modeled, finite element solvers like ComSol and Lumerical are the most accurate, but significantly slower. It is up to the system designer to know which parts of their system fall into the domain of wave optics vs. geometric optics.

The Ray Tracer Program Flow
============================
The ray tracing state machine is composed of three repeating steps: generation, intersection, and interaction.


Generation 
~~~~~~~~~~~
The first step is to generate an initial set of rays being propagated through the system. In renderers, they rays are generated by the camera, with one or more rays for every pixel of the final render, and travel backwards through the scene, and calculating lighting for the surfaces they intersect. Called *backwards ray tracing*, this method is more efficient for renders because every ray ends up as part of the final image. If instead rays were generated from light sources and traced through the system, most of them would never reach the camera and would waste CPU cycles. In a forward ray tracer, the initial set of rays is instead generated by the light sources, and are traced through the system, typically terminating when they hit an absorber or detector. Forward ray tracing is common in engineering because efficiency is a key metric in most optical designs, and the designer needs to know what percentage of light makes it onto their detector. #reword maybe? 

Intersection
~~~~~~~~~~~~~
The next step is find the nearest surface that each ray intersects. This is done by calculating the intersection distance of the ray with every surface in the trace. The surface with the smallest *positive* valued distance is the intersected surface (the value must be positive because rays cannot travel backwards). Common surfaces such as spheres and planes have well documented equations to calculate intersections. More complex surfaces can be discretized into triangular meshes, and the ray checks for an intersection with each triangle.

It's easy to see that as the number of intersections that needs to be calculated is the product of the number of rays multiplied by the number of surfaces. Bounding boxes and convex hulls can be used to significantly speed up ray traces by surrounding a large amount of "subsurfaces" in a single large surface whose intersection is easier to calculate, only if your ray intersects the bounding surface will the intersections of all subsurfaces be checked, otherwise they're ignored. 

Interaction
~~~~~~~~~~~~
Finally, after the software has found the nearest surfaces for each ray, it calls an interaction function. This tells the software what to do with the .... ? In rendering this step involves calling a shader and updating a pixel value in the final image, but it does not have to be limited to just that. in PyRayT, for example, the interaction of a ray with a surface creates a new ray, representing the light's trajectory after interacting with the surface. In idtech1 games the rays did not interact with the surfaces at all, instead the hit distance was used to calculate how tall to draw the walls of the level, giving the illusion of 3D depth to a 2D game. 

A Basic Python implementation
==============================

Using Nested Loops
~~~~~~~~~~~~~~~~~~~

Using Matrices
~~~~~~~~~~~~~~~

Next Steps 
===========




