.. title: Writing an (Overly) Idiomatic Fizzbuzz with Rust
.. slug: rust-fizzbuzz
.. date: 2021-06-22 20:27:33 UTC-04:00
.. tags: 
.. category: 
.. link: 
.. description: 
.. type: text

The last couple few months have been a whirlwind exposure to `Rust`_. It started when I was looking for a systems language to speed up pieces of `PyRayT <https://pyrayt.readthedocs.io>`_ that was more general purpose than `Cython <https://cython.org/>`_, but not C/C++ (which I have my own love/hate relationship with). After reading the excellently written `Rust Book`_ I was hooked on the language, using it for a couple CLIs, a `webserver <https://github.com/rfrazier716/mongo_warp>`_, and even going through old `Advent of Code <https://adventofcode.com/>`_ puzzles to get more practice. 

This post isn't going to be a gushing review of Rust (though as `2020's most loved language <https://insights.stackoverflow.com/survey/2020#technology-most-loved-dreaded-and-wanted-languages-loved>`_ you won't be hard pressed to find one of those either). Instead, it's sparked from an article I saw on `This Week in Rust <https://this-week-in-rust.org/>`_ back in June about writing an `idiomatic binary search <https://shane-o.dev/blog/binary-search-rust>`_. The binary search is a well known algorithm, which got me thinking: what's another well known program I could use to practice writing idiomatic code? The answer: `Fizzbuzz <https://en.wikipedia.org/wiki/Fizz_buzz>`_, the programming puzzle commonly used in interviews to make sure the candidate actually knows what a for loop is. 

In this post I'll be starting with a standard Fizzbuzz solution, and polishing it up to take full advantage of all the features and programming style Rust offers.

.. contents:: 
    :class: alert alert-primary ml-0

.. contents:: Quick Links
    :depth: 2
    :class: alert alert-primary ml-0

What Makes Code Idiomatic?
==========================

Before diving into the *how*, it's worth covering *what* idiomatic code actually is. Outside of coding context, idiomatic means "using, containing, or denoting expressions that are natural to a native speaker." When discussing idiomatic programming, it means the program leverages features unique to the language to accomplish the task. Coming from Python, I would hear this as writing "pythonic" code (`list comprehension`_, `dunder methods`_, etc.). 

.. _`list comprehension`: https://www.w3schools.com/python/python_lists_comprehension.asp
.. _`dunder methods`: https://www.geeksforgeeks.org/dunder-magic-methods-python/

Idiomatic Rust should leverage Rust's unique features such as match, traits, iterators, and ownership. Since I'm still learning Rust every day, I use `Clippy <https://github.com/rust-lang/rust-clippy>`_, a linter with 400+ lints, to catch common mistakes and recommend idiomatic alternatives!

The Basic Fizzbuzz
===================

The goal of Fizzbuzz is simple:

* Write a short program that prints each number from 1 to 100 on a new line. 
* For each multiple of 3, print "Fizz" instead of the number. 
* For each multiple of 5, print "Buzz" instead of the number. 
* For numbers which are multiples of both 3 and 5, print "FizzBuzz" instead of the number.


The first bullet screams "for loop" while the next three are conditional (if statements). With that in mind we'll write our simplest solution relying on a series of if-else statements and the modulo operator.

.. raw:: html

    <div class="rust-playground">
        <a href=https://play.rust-lang.org/?version=stable&mode=debug&edition=2018&gist=4ab45aafc8a95c02010f84f66aabdaaf>
            <i class="fas fa-play"></i> Run on the Rust Playground
        </a>
    </div>

.. code:: rust

    fn main() {
        for x in 1..=100 {
            if x % 3 == 0 && x % 5 == 0 {
                println!("FizzBuzz")
            } else if x % 3 == 0 {
                println!("Fizz")
            } else if x % 5 == 0 {
                println!("Buzz")
            } else {
                println!("{}", x)
            }
        }
    }


This gets us the desired output, but there's nothing idiomatic about it. With the exception of :code:`..=` (specifies a range "up to and including"), none of Rust's unique features are being used. In fact, it looks almost identical to a solution written in Python! Clearly we can do better.

Make Me a Match 
````````````````

If you haven't read `Rust Book`_, bookmark it right away! It's one of the best introductions to a language I've ever read, and explains not just the core language, but the toolchains surrounding it that make Rust so accessible. One thing the book wastes no time introducing is Rust's :code:`match` operator: 

    "Rust has an extremely powerful control flow operator called match that allows you to compare a value against a series of patterns and then execute code based on which pattern matches. Patterns can be made up of literal values, variable names, wildcards, and many other things"

    -- `The Rust Book Ch. 6-2 <https://doc.rust-lang.org/book/ch06-02-match.html>`_

Let's update our basic function to use :code:`match` instead of :code:`if-else`. We want to match the output of two modulo operators, if they're both zero we'll output :code:`Fizzbuzz`, if only one is zero we'll output :code:`Fizz` or :code:`Buzz` depending on the zero. and if neither are zero we'll simply output the number. 

.. raw:: html

    <div class="rust-playground">
        <a href=https://play.rust-lang.org/?version=stable&mode=debug&edition=2018&gist=49150dcded25e25489d34dae9cfad0a3>
            <i class="fas fa-play"></i> Run on the Rust Playground
        </a>
    </div>

.. code:: rust

    fn main() {
        for x in 1..=100 {
            match (x % 3, x % 5) {
                (0, 0) => println!("FizzBuzz"),
                (0, _) => println!("Fizz"),
                (_, 0) => println!("Buzz"),
                _ => println!("{}", x),
            }
        }
    }

Now this is starting to look more like Rust! By using :code:`match` we're able to eliminate a lot of unnecessary brackets and only have to calculate the modulo once, instead of at every if statement. Since the :code:`match` control flow operates from top to bottom, we need the "FizzBuzz" case to be listed first, as both "Fizz" and "Buzz" also satisfy the :code:`(0,0)` case.

Getting Idiomatic
==================

The above code would be more than enough to show an interviewer you passed CS 100, but we want to squeeze every possible idiomatic opportunity out of this function, so our next step will be pulling our logic out of the main function and into a trait. Again referencing the Rust Book:

    "A trait tells the Rust compiler about functionality a particular type has and can share with other types. We can use traits to define shared behavior in an abstract way. We can use trait bounds to specify that a generic can be any type that has certain behavior."

    -- `The Rust Book Ch. 10-2 <https://doc.rust-lang.org/book/ch10-02-traits.html>`_

Right now we're only going to focus one one small feature of traits: defining sets of methods that can be called on a type (in our case :code:`i32`). Our trait :code:`Fizzy` will be simple in that it only has one function (also named :code:`fizzy`) that accepts a reference to the number and returns a String based on our Fizzbuzz rules. 

.. code:: rust

    pub trait Fizzy{
        fn fizzy(&self) -> String;
    }

Trait definitions only declare the methods, they do not define the actual logic. For that we need to *implement* the trait for our selected type. This is as easy as making an :code:`impl` for :code:`i32` and moving the match statement out of our main function into the :code:`fizzy` method. Our new program is shown below with the logic separated out into its own trait.

.. raw:: html

    <div class="rust-playground">
        <a href=https://play.rust-lang.org/?version=stable&mode=debug&edition=2018&gist=b2f1e2702441ebb90ededd28ae91959d>
            <i class="fas fa-play"></i> Run on the Rust Playground
        </a>
    </div>

.. code:: rust

    pub trait Fizzy {
        fn fizzy(&self) -> String;
    }

    impl Fizzy for i32 {
        fn fizzy(&self) -> String {
            match (self % 3, self % 5) {
                (0, 0) => String::from("FizzBuzz"),
                (0, _) => String::from("Fizz"),
                (_, 0) => String::from("Buzz"),
                _ => format!("{}", self),
            }
        }
    }

    fn main() {
        for x in 1..=100 {
            println!("{}", x.fizzy())
        }
    }


It may look like all we did was shuffle around where the code was (and for this simple of a program traits are already overkill) but structuring our logic into a trait allows for flexibility down the road, especially if we have to add more methods to :code:`Fizzy` or define it for different types (imagine a new Fizzbuzz with letters instead of numbers). The separation also allows us to write unit tests to validate :code:`fizzy` since it can be called separately from the main function.

Idiomatic Testing???
`````````````````````

Unit tests themselves are not particularly idiomatic to Rust. In fact, you'd be hard pressed to find a modern language that does not have an extensive unit-test framework to tap into. What *is* idiomatic, however, is how testing is built into the core language and Rust's solution to testing private interfaces.

When writing an class/interface, I'll split complex methods into multiple small methods that can be easily tested, but I don't want those interim methods exposed to the end user. Python makes this easy enough with private methods, prefixing a function with an underscore (_) marks it as private, and most documentation and linters will treat it as such. However, it's actually as public as any other function, so while the IDE might flag a warning when I call the method to test it, there's nothing illegal about doing so (see below).

.. code:: Python

    class Greeter(object):
        
        def __init__(self, name):
            self.name = name
        
        # putting an _ before a method marks it as private     
        def _address(self, preamble: str) -> None:
            print(f"{preamble} {self.name}")
            
        def hello(self) -> None:
            self._address("Hello") # a public interface can call a private method


    if __name__ == '__main__':
        greeter = Greeter("Fotonix")
        greeter.hello() # this instance method is public
        greeter._address("Buongiorno") # this method is private, but can still be called

    #-- Output --
    # Hello Fotonix
    # Buongiorno Fotonix


On the opposite side of the accessability spectrum we have C++, which uses its `public, private, and protected`_ keywords to strictly enforce what objects and classes have access to those methods. While this is great from a security standpoint, it makes testing non-public interfaces difficult because you either have to (1) accept that you can only write "blackbox tests" that test the interfaces end users have, or (2) create `friend classes <https://www.geeksforgeeks.org/friend-class-function-cpp/>`_ that wrap the private functions in a public interface, and test that new interface.

.. _`public, private, and protected`: https://stackoverflow.com/questions/860339/difference-between-private-public-and-protected-inheritance 

Rust strikes a happy medium between the two. You can still declare traits as public or private, and that privacy is not only respected, but enforced at compile-time. However, using the `modules <https://doc.rust-lang.org/book/ch07-02-defining-modules-to-control-scope-and-privacy.html>`_ system, you can put your tests in a path that has access to the private traits (i.e. they're within the trait's scope). 

The most common way to do this is to *inline unit tests in the same file as the methods you're testing* and wrapping them in a module called :code:`test`. Apart from this unique layout, writing the tests themselves is similar to most unit-test frameworks. Rust has built-in macros for assertions and tests can be separated into functions to run concurrently. We'll add unit-tests to the bottom of our Fizzbuzz program to validate the :code:`Fizzy` trait. Tests can by run by running :code:`cargo test` from the terminal, or "test" from the pull-down menu in the playground.


.. raw:: html

    <div class="rust-playground">
        <a href=https://play.rust-lang.org/?version=stable&mode=debug&edition=2018&gist=0903c09a16ab46e0fbc66beb3129280e>
            <i class="fas fa-play"></i> Run on the Rust Playground
        </a>
    </div>

.. code:: rust

    #[cfg(test)]
    mod test {
        use super::*;

        #[test]
        fn test_fizz() {
            for x in &[3, 6, 27] {
                assert_eq!(x.fizzy(), "Fizz")
            }
        }

        #[test]
        fn test_buzz() {
            for x in &[5, 10, 20] {
                assert_eq!(x.fizzy(), "Buzz")
            }
        }

        #[test]
        fn test_fizzbuzz() {
            for x in &[15, 30, 60] {
                assert_eq!(x.fizzy(), "FizzBuzz")
            }
        }

        #[test]
        fn test_num() {
            for x in &[13, 29, 98] {
                assert_eq!(x.fizzy(), format!("{}", x))
            }
        }
    }

Generic Traits and Monomorphization
====================================

At this point pulling out the above Fizzbuzz will knock any interviewer's socks clean off... or they'll be annoyed that you've spend so much time on such an easy question, could go either way. But we're not here to please an imaginary interviewer! We're writing the most idiomatic Fizzbuzz in the history of Rust, so let's add one more "*totally unnecessary in this context but useful in general*" feature: Generic Types. 

Up until now we've used :code:`i32` as the base type for all things fizzbuzz. It's a safe bet for general integers, having a range of >4 billion, but will it always be the *right* choice for our program? If fizzbuzz will only ever use positive numbers, you may as well use an unsigned int. If you only ever need to calculate up to 100, 32-bits is overkill and you're better off with :code:`u8`. Instead of trying to predict the end use-case, we want to write our trait implementation such that the main function can call it with *any* integer type, and an appropriate trait method is called. 

Rust solves this issue with `generics <https://doc.rust-lang.org/book/ch10-01-syntax.html>`_. Instead of defining a function for a specific type, the programmer defines a set of traits that the type **must** implement. Generics are one of Rust's *zero-cost abstractions*, and provide flexibility while incurring `no overhead at runtime <https://doc.rust-lang.org/book/ch10-01-syntax.html#performance-of-code-using-generics>`_.

To make :code:`Fizzy` generic to all int types, we'll use the `num <https://crates.io/crates/num>`_ crate. The trait we want is :code:`PrimInt` which is a general abstraction for integer types, and :code:`Zero` which will generate the zero value we compare to. We also need the :code:`Display` trait from the standard library, which enforces that the type can be formatted into a string. 


.. raw:: html

    <div class="rust-playground">
        <a href=https://play.rust-lang.org/?version=stable&mode=debug&edition=2018&gist=8305e2bdd08c0da94542fc3a8d670a7c>
            <i class="fas fa-play"></i> Run on the Rust Playground
        </a>
    </div>

.. code:: rust

    use num_traits::{identities::Zero, PrimInt}; // 0.2.14

    pub trait Fizzy {
        fn fizzy(&self) -> String;
    }

    impl<T> Fizzy for T
    where
        T: PrimInt + Zero,
        T: Copy + Clone,
        T: std::fmt::Display,
    {
        fn fizzy(&self) -> String {
            let zero = T::zero();
            let three = T::from(3).unwrap(); // These will never fail
            let five = T::from(5).unwrap();
            match (*self % three, *self % five) {
                (x, y) if x == zero && y == zero => String::from("FizzBuzz"),
                (x, _) if x == zero => String::from("Fizz"),
                (_, x) if x == zero => String::from("Buzz"),
                _ => format!("{}", self),
            }
        }
    }

    fn main() {
        for x in 1..=100 {
            println!("{}", x.fizzy())
        }
    }

Notice how we can no longer use integers in :code:`fizzy`, but instead have to convert them to our generic type within the function. Fortunately the compiler optimizes this out and replaces them with constants in the final code. This is also a case where its acceptable to use :code:`unwrap` without fear of causing a panic at runtime. Since T implements :code:`PrimInt` we know a conversion from integers to T will never fail.

Going off the Deep End 
=======================

We did it, we wrote an amazing Fizzbuzz leveraging a slew of Rust's unique features! But we also cheated slightly... The rules of the game asked us to print the result of the fizzbuzz check, but to enable testing we return a :code:`String` that's printed in the main loop. We can trim down this waste of a *whopping 72 bytes* of memory by having :code:`fizzy` write directly to an IO stream! The easiest solution would be to have our function call the :code:`println!` macro directly, but then we can no longer test our function. Instead, We'll borrow a tip from the `Rust CLI Book <https://rust-cli.github.io/book/tutorial/testing.html#making-your-code-testable>`_ (different than *The Rust Book*, but equally as good) where we pass a mutable reference to a :code:`Writer` handle. In the main loop that handle will point to stdout, but for testing it will be a :code:`vector` that we can compare to the expected output.

This requires a couple modifications to our :code:`fizzy` function, (1) we need to replace all the match statement arms with :code:`writeln!` macro calls. and (2) since :code:`writeln!` can fail we need to modify the signature of :code:`fizzy` to return a :code:`std::io::Result` enum, allowing us to squeeze in yet another idiomatic feature: Error Types! We also want to be able to catch the error in the main function. so we'll replace the for loop with an iterator, and consume it with a :code:`try_for_each` method.


.. raw:: html

    <div class="rust-playground">
        <a href=https://play.rust-lang.org/?version=stable&mode=debug&edition=2018&gist=df1f2f10f63bc1eed011574e4ce5ba31>
            <i class="fas fa-play"></i> Run on the Rust Playground
        </a>
    </div>

.. code:: rust

    use num_traits::{identities::Zero, PrimInt}; // 0.2.14
    use std::io::{Result, Write};

    pub trait Fizzy {
        fn fizzy(&self, writer: &mut impl Write) -> Result<()>;
    }

    impl<T> Fizzy for T
    where
        T: PrimInt + Zero,
        T: Copy + Clone,
        T: std::fmt::Display,
    {
        fn fizzy(&self, writer: &mut impl Write) -> Result<()> {
            let zero = T::zero();
            let three = T::from(3).unwrap(); // THese will never fail
            let five = T::from(5).unwrap();
            match (*self % three, *self % five) {
                (x, y) if x == zero && y == zero => writeln!(writer, "FizzBuzz"),
                (x, _) if x == zero => writeln!(writer, "Fizz"),
                (_, x) if x == zero => writeln!(writer, "Buzz"),
                _ => writeln!(writer, "{}", self),
            }
        }
    }

    fn main() {
        let mut out = std::io::stdout();
        if let Err(error) = (1..=100).try_for_each(|x| x.fizzy(&mut out)) {
            println!("IO Error Writing to Stream: {}", error)
        }
    }

With those small changes we've added mutable references, iterators, and error handling to the list of features this little program can demonstrate. Was any of it necessary? Not at all! Our final output is no different than the first program composed of if-else statements. But it's always fun to start with a trivial program and think up ways to transform it into something that makes me feel like I'll one day earn the title of "Rustacean".    


.. _`Rust`: https://www.rust-lang.org/
.. _`Rust Book`: https://doc.rust-lang.org/book/