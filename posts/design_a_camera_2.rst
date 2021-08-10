.. title: Design a Camera with Python and PyRayT: Part Two
.. slug: design-a-camera-with-python-and-pyrayt-part-two
.. date: 2021-08-10 11:20:32 UTC-04:00
.. tags: 
.. category: 
.. link: 
.. description: 
.. type: text
.. status: draft

.. contents:: 
    :class: alert alert-primary ml-0

.. contents:: Quick Links
    :depth: 2
    :class: alert alert-primary ml-0

Adding Another Lens
=================================

We've characterized the flaws in our single lens solution, now what? We need some free variables we can tune to minimize aberrations. One thought might be to adjust the two radii of curvature and lens thickness, and while we can definitely reduce spherical aberration and coma, chromatic aberration is a function of the lens material's dispersion, and no variation of the mechanical properties will eliminate it. Instead, we're going to borrow a very well known design: the `doublet lens <https://en.wikipedia.org/wiki/Doublet_(lens)>`_. 

Doublets use two different dispersive materials to cancel out chromatic aberration, and the four radii of curvature can be optimized to suppress our other aberrations. Before passing everything off to an optimizer, however, we need to derive initial values for our design.

Lens power and Abbe Numbers
----------------------------

When designing the single lens imager, we made a point to specify the system power instead of focus. This is because for thin lenses *the power of a system is roughly equal to the sum of the power of each component*. Meaning our two lens solution must satisfy the equation:

.. math::

    \Phi_1 + \Phi_2 = \Phi_{sys}

where :math:`\Phi_n` is the power of the nth component. The other aberration we can correct for while using thin-lens approximations is chromatic: we want the dispersion of one lens to be canceled by the dispersion of the second. We could hand-derive :math:`\frac{d\Psi}{d\lambda}` for each material and set those sums equal to zero, but luckily for us `Ernst Abbe <https://en.wikipedia.org/wiki/Ernst_Abbe>`_ did that in the 1860's a standardized metric called `Abbe numbers <https://en.wikipedia.org/wiki/Abbe_number>`_, stylized as :math:`V`. 

The change in refractive power is inversely proportional to the V-number, so our constraint to cancel chromatic aberration becomes:

.. math::

    \frac{\Phi_1}{V_1} + \frac{\Phi_2}{V_2} = 0


With two equations and two unknowns we can solve for the power of each lens as a function of abbe numbers.
The change in power 
