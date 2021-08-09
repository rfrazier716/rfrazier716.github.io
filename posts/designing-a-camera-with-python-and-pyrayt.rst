.. title: Design a Camera with Python and PyRayT
.. slug: design-a-camera-with-python-and-pyrayt
.. date: 2021-08-05 21:04:29 UTC-04:00
.. tags: 
.. category: 
.. link: 
.. description: 
.. has_math: true
.. type: text

Opening Blurb!

.. contents:: 
    :class: alert alert-primary ml-0

.. contents:: Quick Links
    :depth: 2
    :class: alert alert-primary ml-0


Why Are Camera Lenses so Complex?
==================================

Optical Aberrations
--------------------

Brushing up on the Basics
==========================

Creating a Simple Camera
=========================

The first step to designing our camera is to start with a simple, single lens solution that we can iterate on. The only specs we need to decide on right now are the power and f/# (`F-number <https://en.wikipedia.org/wiki/F-number>`_) of the system. We want the system to have a focal length of 50mm, and since a lens' power is the inverse of focal length, our system power is 0.02. Our f/# will be 2.4, meaning the focal length should be 2.4x larger than the entrance aperture. With those numbers in hand we're ready to define our camera!

Thin Lenses 
------------

Our lens is the only component that contributes to system power, so the power of the lens has to equal the desired power of our system. We'll use the `lensmaker's equation <https://en.wikipedia.org/wiki/Lens#Lensmaker's_equation>`_.

.. math::

    P_{lens} = (n_{lens} -1)[\frac{1}{R_1}-\frac{1}{R_2}+\frac{(n_{lens}-1)d}{n R_1 R_2}]

Since we're doing the calculation by hand we'll make a couple approximations to simplify the design: (1) the radii of curvature are equal and opposite (resulting in a biconvex lens), and (2) the thickness is small enough that we can discard the final term. Later we'll numerically optimize the entire system to correct for focus as well as aberrations, but these approximations give us a good starting point.

The simplified equation then becomes:

.. math::

    R_{lens} =\frac{2(n_{lens} -1)}{P_{lens}}

Since the refractive index of most glasses is ~1.5, this means that our radius of curvature for a biconvex lens is equal to the *inverse of the lenses power*, which is also the focal length of the system!

Now we can build our lens in *PyRayt* and visualize it with the :code:`draw` function in the :code:`tinygfx` package (installed as part of the PyRayT distribution).

.. code:: python

    # import the Ray Tracer Package
    import pyrayt
    import pyrayt.materials as matl
    from tinygfx.g3d.renderers import draw

    # All spatial units are mm
    lens_diameter = 30
    lens_thickness = 5
    system_focus = 50 # The focus of the system
    f_num = 2.4 # f-number of system

    # Creating a simple Lens 
    lens_material = matl.glass["ideal"]
    lens_radius = 2*(lens_material.index_at(0.633)-1)*system_focus
    lens = pyrayt.components.thick_lens(
        r1=lens_radius, 
        r2=-lens_radius,
        thickness=lens_thickness,
        aperture=lens_diameter,
        material=lens_material)

    draw(lens)

.. image:: /images/camera_design_with_pyrayt/biconvex_lens.png
    :align: center

A lens is not too impressive by itself. Lets add the remaining parts of our system so we can start running ray traces!

Apertures and Baffles
----------------------

There's two more pieces we need in order to make the camera: an aperture to block rays that exceed our f/# and an imager placed on our camera's focal plane. From a modeling perspective both will be accomplished with variations of PyRayT's :code:`baffle`. Baffle's are 2D planes that absorb all light incident on them, perfect for modeling sensors as well as ideal beam-stops. For the imager we create a square baffle the same size as our lens and move it to the focal plane.

.. code:: python

    imager = components.baffle((lens_diameter, lens_diameter)).move_x(system_focus)

Our aperture can be thought of as a "baffle with a hole", where the hole is large enough to only let in rays with a cone angle specified by our f/#. :code:`pyrayt` and :code:`tinygfx` create arbitrary shapes via `constructive solids </posts/efficient-csg/>`_ so an aperture is a baffle with the center shape subtracted from it. The convenience function :code:`aperture` does just this, creating a baffle with an arbitrarily shaped hole in the middle. 

The diameter of the aperture that gives us the desired f/# depends on where in the system the aperture is located. If we place it half-way between the lens and the focal plane, the diameter of the opening has to be:

.. math::
    
    d_{ap}=\frac{1}{2*P_{sys}}*\frac{1}{f_\#}

.. code:: python 

    aperture_position = system_focus / 2
    aperture_diameter = aperture_position / f_num

    aperture = components.aperture(
        size=(lens_diameter, lens_diameter), # make a square baffle
        aperture_size=aperture_diameter # put a circular opening in the center
        ).move_x(aperture_position)


Our First Ray Trace
--------------------

With our components defined we're ready to simulate. The only thing we need is a test source that generates rays to trace through the system. PyRayT's :code:`LineOfRays` is perfect for this, as it generates a set of linearly spaced rays projected towards the +x axis. The last step is to load all the components into a :code:`RayTracer` object and run the :code:`trace` function.

.. container::
    class: alert alert-info

    Almost all of the sources used to characterize our system will be parallel bundles of rays at various angles. This is because we're assuming the camera is `focused at infinity <https://en.wikipedia.org/wiki/Infinity_focus>`_, where any angular deviation between sets of rays originating from the same point are effectively zero.

.. code:: python

    # Create a Parallel ray set
    source = components.LineOfRays(0.8*lens_diameter, wavelength = 0.633).move_x(-10)

    tracer = pyrayt.RayTracer(source, [lens, aperture, imager])
    tracer.set_rays_per_source(11)
    results = tracer.trace()

The results of a trace is a `Pandas <https://pandas.pydata.org/>`_ dataframe which stores information about the ray at every intersection of the simulation. However, for now we'd rather just visualize the ray trace, which is done with the :code:`show` function.

.. code:: python

    # import matplotlib so we can manipulate the axis
    import matplotlib.pyplot as plt

    # set up the figure and axis
    fig = plt.figure(figsize=(12,12))
    axis = plt.gca()
    axis.set_xlabel("distance (mm)")
    axis.set_ylabel("distance (mm)")


    # display the ray trace
    tracer.show(
        ray_width=0.2,
        axis=axis,
        view='xy')
    plt.show()

.. image:: /images/camera_design_with_pyrayt/single_lens_raytrace.png
    :align: center

Looks like our lens is doing its job! All rays that transmit through the aperture are focused to an approximate point at the focal distance, and any ray angle that exceeds our f/# is blocked. Unfortunately since the aperture and imager are 2D objects, they don't show up in the ray trace, but we know that they are there because rays terminate on their surfaces. 

Characterizing Lens Performance
--------------------------------

A picture may be worth 1000 words, but when it comes to analyzing our lens' performance data is key. An optimum imager design should minimize common imaging aberrations (namely spherical, chromatic, and coma). lets see how our single lens design holds up in each of these cases.

Spherical Aberrations
``````````````````````

spherical lenses don't actually focus light to a perfect point. In fact, the focal point is a function of the radius where the light enters the lens (in our case the position on the y-axis where the ray originates). We can easily visualize the spherical aberrations by creating a helper function that generates a set of rays along the y-axis, and calculates where each ray intercepts the x-axis.

.. code:: python

    def spherical_aberration(system, ray_origin: float, max_radius:float, sample_points=11):

        # the souce is a line of rays only on the +y axis. It's slightly shifted so zero is not a point
        # as it would focus at infinity
        source = pyrayt.components.LineOfRays(0.9*max_radius).move_x(ray_origin).move_y(max_radius/2)


        tracer = pyrayt.RayTracer(source, system)
        tracer.set_rays_per_source(sample_points)
        results = tracer.trace()

        # Since we don't have the actual imager as a variable in the function
        # assume it is the last thing a ray intersect with, meaning the rays that hit it have the 
        # highest generation
        imager_rays = results.loc[results['generation'] == np.max(results['generation'])]
        
        # Intercept is calculated using the tilt for each ray, with is a normalized vector representing
        # the direction the ray is travelling
        intercept = -imager_rays['x_tilt']*imager_rays['y0']/imager_rays['y_tilt'] + imager_rays['x0']

        # the original radii 
        radii = results.loc[np.logical_and(results['generation']==0, results['id'].isin(imager_rays['id']))]['y0']

        # create a new dataframe with the aberration metrics
        results = pd.DataFrame({'radius': np.asarray(radii), 'focus': np.asarray(intercept)})
        return results

Using the function on our single-lens system yields the following plot.

.. image:: /images/camera_design_with_pyrayt/spherical_aberration_chart_single_lens.png
    :align: center

This plot shows that the focal length of the lens is changing by almost 10% based on the radius alone, resulting in poor image quality with pictures looking "blurry" even when the imager is aligned to the focal plane. Speaking of the focal plane, we also see that the focus of our lens is ~53mm instead of the 50 we calculated. This is coming from the thick lens portions of the lensmaker's equation which we chose to ignore.


Chromatic Aberrations
``````````````````````

Unlike spherical aberrations, chromatic aberrations are explained by the lensmaker's equation: the focal point of the lens depends on the refractive index of the lens' material. Real materials don't have a constant refractive index; instead, the refractive index is a function of wavelength. This effect is called `dispersion <https://en.wikipedia.org/wiki/Dispersion_(optics)>`_, and while it's more often associated with the reason prisms create rainbows, it also means our lens will have a wavelength dependent focus.

The same way we wrote a function to characterize spherical aberrations, we can write one to quantify chromatic aberration:

.. code:: python

    def chromatic_abberation(system, ray_origin: float, test_radius:float, wavelengths: np.ndarray) -> pd.DataFrame:
        # create a set of sources for every wavelength of light
        sources = [
            pyrayt.components.LineOfRays(0, wavelength = wave)
            .move_y(test_radius)
            .move_x(ray_origin) 
            for wave in wavelengths]
        
        # Create the ray tracer and propagate
        tracer = pyrayt.RayTracer(sources, system)
        tracer.set_rays_per_source(1)
        results = tracer.trace()

        #filter the rays that intersect the imager
        imager_rays = results.loc[results['generation'] == np.max(results['generation'])]
        
        # calculate intercept of the imager rays with the x-axis and form into a dataframe
        intercept = -imager_rays['x_tilt']*imager_rays['y0']/imager_rays['y_tilt'] + imager_rays['x0']
        results = pd.DataFrame({'wavelength': imager_rays['wavelength'], 'focus': intercept})

        return results


If we run this function on our current system the results will say that every wavelength has the exact same focus! This is because we made the lens out of an "ideal" glass with a refractive index (n) of 1.5. Let's replace our lens with one made of a popular crown glass instead

.. code:: python
    
    lens_material = matl.glass["BK7"] # Update this line of the lens definition

Running the function on our newly dispersive system shows a focal length shift of ~1mm (2%) across the visible spectrum.

.. container:: alert alert-warning
    
    plot of chromatic aberration
    
An image taken with this lens would result in sharp edges in our photos having a 'rainbow' effect. interstingly, this aberration is sometimes saught after for artistic effect, going as far as being including as a graphics setting in id's 2016 Doom reboot.


Coma Aberrations
`````````````````

Coma is a unique aberration: instead of being a change in focal length, it's a change mangification vs. angle of incidence on the system. The name comes from the fact that points imaged with a system suffering from coma looks like the `coma of a comet <https://en.wikipedia.org/wiki/Coma_(cometary)>`_.

The easiest way to visualize coma is to look at in in our system. To do this we'll construct 3 parallel sources that enter the system at different angles.



Adding Another Lens
=================================

Lens power and Abbe Numbers
----------------------------