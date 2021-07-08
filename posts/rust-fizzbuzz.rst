.. title: Writing an (Overly) Idiomatic Fizzbuzz with Rust
.. slug: rust-fizzbuzz
.. date: 2021-06-22 20:27:33 UTC-04:00
.. tags: 
.. category: 
.. link: 
.. description: 
.. type: text

The last couple few months have been a whirlwind exposure to `Rust`_. It started when I was looking for a systems language to speed up pieces of `PyRayT <https://pyrayt.readthedocs.io>`_ that was more general purpose than `Cython <https://cython.org/>`_, but was not c/c++ (which I have my own love/hate relationship with). After reading the excellently written `Rust Book`_ I was hooked on the language, using it for a couple CLIs, a webserver, and even going through old Advent of Code puzzles to get more practice. 

This post isn't going to be a gushing review of Rust (though as `2020's most loved language <https://insights.stackoverflow.com/survey/2020#technology-most-loved-dreaded-and-wanted-languages-loved>`_ you won't be hard pressed to find one of those either). Instead, it's sparked from an article I saw on `This Week in Rust <https://this-week-in-rust.org/>`_ back in June about writing an `idiomatic binary search <https://shane-o.dev/blog/binary-search-rust>`_. The binary search is a well known algorithm, which got me thinking: what's another well known program I could use to practice writing idiomatic code? The answer: `Fizzbuzz <`, the programming puzzle commonly used in interviews to make sure the candidate actually knows what a for loop is. 

In this post I'll be starting with a standard Fizzbuzz solution, and polishing it up to take full advantage of all the features and programming style Rust offers.

.. contents:: 
    :class: alert alert-primary ml-0

.. contents:: Quick Links
    :depth: 2
    :class: alert alert-primary ml-0

What Makes Code Idiomatic?
==========================

Before diving into the *how*, it's worth covering *what* idiomatic code actually is. Outside of coding context, idiomatic means *using, containing, or denoting expressions that are natural to a native speaker*. When discussing idiomatic programming, it means the program leverages features unique to the language to accomplish the task. Coming from Python, I would hear this as writing "pythonic" code (list comprehension, dunder methods etc.). 

Idiomatic Rust should leverage Rust's unique features such as match, traits, iterators, and ownership. If you want to improve your own idiomatic Rust, `Clippy <https://github.com/rust-lang/rust-clippy>`_ is a linter with 400+ lints to catch common mistakes and recommend idiomatic alternatives!

The Basic Fizzbuzz
===================

The goal of Fizzbuzz is simple:

* Write a short program that prints each number from 1 to 100 on a new line. 
* For each multiple of 3, print "Fizz" instead of the number. 
* For each multiple of 5, print "Buzz" instead of the number. 
* For numbers which are multiples of both 3 and 5, print "FizzBuzz" instead of the number.


The first bullet screams "for loop" while the next three are conditional (if statements). With that in mind we'll write our simplest solution relying on a series of if-else statements and the modulo operator.

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

`Run on the Rust Playground <https://play.rust-lang.org/?version=stable&mode=debug&edition=2018&gist=4ab45aafc8a95c02010f84f66aabdaaf>`_

This gets us the desired output, but there's nothing idiomatic about it. With the exception of :code:`..=` (specifies a range "up to and including"), none of Rust's unique features are being used. In fact, it looks almost identical to a solution written in Python! Clearly we can do better.

Make Me a Match 
````````````````

If you haven't read `Rust Book`_, bookmark it right away! It's one of the best introductions to a language I've ever read, and explains not just the core language, but the toolchains surrounding it that make Rust so accessible. One thing the book wastes no time introducing is Rust's :code:`match` operator: 

    "Rust has an extremely powerful control flow operator called match that allows you to compare a value against a series of patterns and then execute code based on which pattern matches. Patterns can be made up of literal values, variable names, wildcards, and many other things"

    -- `The Rust Book Ch. 6-2 <https://doc.rust-lang.org/book/ch06-02-match.html>`_

Lets update our basic function to use :code:`match` instead of :code:`if-else`. We want to match the output of two modulo operators, if they're both zero we'll output :code:`Fizzbuzz`, if only one is zero we'll output :code:`Fizz` or :code:`Buzz` depending on the zero. and if neither are zero we'll simply output the number. 

`Run on the Rust Playground2 <https://play.rust-lang.org/?version=stable&mode=debug&edition=2018&gist=49150dcded25e25489d34dae9cfad0a3>`_

.. code:: rust

    fn main() {
        for x in 1..=100 {
            match (x % 3, x % 5){
                (0, 0) => println!("FizzBuzz"),
                (0, _) => println!("Fizz"),
                (_, 0) => println!("Buzz"),
                _ => println!("{}", x)
            }
        }
    }

Now this is starting to look more like Rust! By using :code:`match` we're able to eliminated a lot of unnecessary brackets and only have to calculate the modulo once, instead of at every if statement. Since the match control flow operates from top to bottom, we need the "FizzBuzz" case to be listed first, as both "Fizz" and "Buzz" also satisfy the :code:`(0,0)` case.

Getting Idiomatic
==================

The above code would be more than enough to show an interviewer you passed CS 100, but we want to squeeze every possible idiomatic opportunity out of this function, so our next step will be pulling our logic out of the main function, and into a trait. To quote the Rust Book again:

    "A trait tells the Rust compiler about functionality a particular type has and can share with other types. We can use traits to define shared behavior in an abstract way. We can use trait bounds to specify that a generic can be any type that has certain behavior."

    -- `The Rust Book Ch. 10-2 <https://doc.rust-lang.org/book/ch10-02-traits.html>`_

Right now we're only going to focus one one small feature of traits: defining sets of methods that can be called on a type (in our case :code:`i32`). Our trait :code:`Fizzy` will be simple in that it only has one function (also named :code:`fizzy`) that accepts a reference to the number and returns a String based on our Fizzbuzz rules. 

.. code:: rust

    pub trait Fizzy{
        fn fizzy(&self) -> String;
    }

Trait definitions only *declare* the methods, they do not define the actual logic. For that we'll need to implement the trait for our selected type. This is as easy as making an :code:`impl` for :code:`i32` and moving the match statement out of our main function into the :code:`fizzy` method. Our new program is shown below with the logic separated out into its own trait.

https://play.rust-lang.org/?version=stable&mode=debug&edition=2018&gist=b2f1e2702441ebb90ededd28ae91959d

.. code:: rust

    pub trait Fizzy{
        fn fizzy(&self) -> String;
    }

    impl Fizzy for i32 {
        fn fizzy(&self) -> String{
            match (self % 3, self % 5){
                (0, 0) => String::from("FizzBuzz"),
                (0, _) => String::from("Fizz"),
                (_, 0) => String::from("Buzz"),
                _ => format!("{}", self)
            }
        }
    }

    fn main() {
        for x in 1..=100 {
            println!("{}", x.fizzy())
        }
    }


This may look like all we did was shuffle around where the code was (and for our simple program it's likely overkill) but structuring our logic into a trait allows for flexibility down the road, especially if we have to add more methods to the fizzy trait, or define it for different types (imagine a new fizzbuzz with letters instead of numbers). The separation also allows us to write unit-tests to validate :code:`fizzy` since it can be called separately from the main method.

Writing Unit Tests
```````````````````

Unit tests themselves are not particularly "idiomatic" to Rust. In fact, you'd be hard pressed to find a modern language that does not have an extensive unit-test framework to tap into. What *is* idiomatic, however, is how testing is built into the core language Rust's solution to testing private interfaces.

When writing an class/interface, I'll split complex methods into multiple small methods that can be easily tested, but I don't want those interim methods exposed to the end user. Python makes this easy enough with private methods, prefixing a function with an underscore (:code:`_`) marks it as private, and most documentation and linters will treat it as such. However, it's actually as public as any other function, so while the IDE might flag a warning when I call the method to test it, there's nothing illegal about doing so (see below).

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


On the opposite side of the accessability spectrum we have c++, which uses its `public, private, and protected`_ keywords to strictly enforce what objects and classes have access to those methods. While this is great from a security standpoint, it makes testing non-public interfaces difficult because you either have to (1) accept that you can only write "blackbox tests" that test the interfaces end users have, or (2) create `friend classes <https://www.geeksforgeeks.org/friend-class-function-cpp/>`_ that wrap the private functions in a public interface, and test that new interface.

.. _`public, private, and protected`: https://stackoverflow.com/questions/860339/difference-between-private-public-and-protected-inheritance 

Rust strikes a happy medium between the two. You can still declare traits as public or private, and that privacy is not only respected, but enforced at compile-time. However, using the `modules <https://doc.rust-lang.org/book/ch07-02-defining-modules-to-control-scope-and-privacy.html>`_ system, you can put your tests in a path that has access to the private traits (e.g. they're within the trait's scope). 

The most common way to do this is to *inline unit tests in the same file as the methods you're testing* and wrapping them in a module called :code:`test`. Apart from this unique layout, writing the tests themselves is similar to most unit-test frameworks. Rust has built-in macros for assertions and tests can be separated into functions to run concurrently. We'll add unit-tests to the bottom of our Fizzbuzz program to validate the :code:`Fizzy` trait. Tests can by run by running :code:`cargo test` from the terminal, or "test" from the pull-down menu in the playground.

https://play.rust-lang.org/?version=stable&mode=debug&edition=2018&gist=0903c09a16ab46e0fbc66beb3129280e

.. code:: rust

    #[cfg(test)]
    mod test{
        use super::*;

        #[test]
        fn test_fizz(){
            for x in vec![3,6,27]{
                assert_eq!(x.fizzy(), "Fizz")
            }
        }
        
        #[test]
        fn test_buzz(){
            for x in vec![5, 10, 20]{
                assert_eq!(x.fizzy(), "Buzz")
            }
        }
        
        #[test]
        fn test_fizzbuzz(){
            for x in vec![15, 30, 60]{
                assert_eq!(x.fizzy(), "FizzBuzz")
            }
        }
    }

Generic Traits and Monomorphization
====================================

At this point you've likely knocked the interviewer's socks clean off. Not only do you know the trendy new systems language, but you clearly understand the importance of test driven development! Just sprinkle in a couple references to the latest frameworks during the Q&A section and the job is in the bag. Before we leave the program be, however, we're going to add one more feature that will ensure they think you're up to snuff with rust: Generic Types. 

Up until now we've used :code:`i32` as the base type for all things fizzbuzz. It's a safe bet for general integers, having a range of >4 billion, but will it always be the *right* choice for our program? If fizzbuzz will only ever use positive numbers, you may as well use an unsigned int. If you only ever need to calculate up to 100, 32-bits is overkill and you're better off with :code:`u8`. Instead of trying to predict the end use-case, we want to write our trait implementation such that the main function can call it with *any* integer type, and an appropriate trait method is called. 

Rust solves this issue with `generics <https://doc.rust-lang.org/book/ch10-01-syntax.html>`_. Instead of defining a function for a specific type, the programmer defines a set of traits that the type **must** implement. Generics are one of Rust's *zero-cost abstractions*, and provide flexibility while incurring `no overhead at runtime <https://doc.rust-lang.org/book/ch10-01-syntax.html#performance-of-code-using-generics>`_.

To make :code:`Fizzy` generic to all int types, we'll use the `num <https://crates.io/crates/num>`_ crate. The trait we want is :code:`PrimInt` which is a general abstraction for integer types, and :code:`Zero` which will generate the zero value we compare to. We also need the :code:`Display` trait from the standard library, which enforces that the type can be formatted into a string. 

https://play.rust-lang.org/?version=stable&mode=debug&edition=2018&gist=291c591a443578e3f803837d45bdf44c

.. code:: rust

    use num_traits::{identities::Zero, PrimInt}; // 0.2.14

    pub trait Fizzy {
        fn fizzy(&self) -> String;
    }

    impl<T> Fizzy for T
    where
        T: PrimInt + Zero,
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
        for (xi32, xu8) in (1..=30).zip(1u8..) {
            println!("{}\t{}", xi32.fizzy(), xu8.fizzy())
        }
    }

Notice how we can no longer use integers in :code:`fizzy`, but instead have to convert them to our generic type within the function. Fortunately the compiler optimizes this out and replaces them with constants in the final code. This is also a case where its acceptable to use :code:`unwrap` without fear of causing a panic at runtime. Since T implements :code:`PrimInt` we know a conversion from integers to T will never fail.

... WRITE A CLEVER CONCLUSION YA GIT


.. _`Rust`: https://www.rust-lang.org/
.. _`Rust Book`: https://doc.rust-lang.org/book/