

CodeHealth Project
===

Original Authors
---

Chris Buonocore
Victor Kwan


Prototype Design
---

*A one-pager for the programming language design you will be prototyping in your project. This can be an entirely new design, or one of the designs that you presented in class. Either way, you must have a *concrete design*, not just a nebulous idea of what you want to do -- the latter will make it really difficult for you to do a good job on the project. So even if you're exploring an "old" design, you'll probably want to revise the original one-pager to make it more concrete.*


Motivation
---

##### What design questions will this project seek to answer?

1. Comment maintenance is often a secondary priority when it comes to making code changes. We want to be able to visualize how often comments go stale in codebases.
2. How can we better enforce programmer's updates to comments when the definition of the underlying code has changed?
3. Will developers find the health scores useful in terms of understanding what comments are new and up-to-date and what could potentially be stale (or no longer valid)?
4. How feasible is it to create a somewhat language-agnostic platform for analyzing comment health scores?
5. How feasible is it to create an accurate comment health scoring model (that runs in reasonable time)?

#####  What is the plan of attack, i.e., how does the codehealth system go about finding answers to the questions listed above?


1. Construct a source code parser that will lookup the commit history of the current file you are viewing
2. Extract the comments from the file into Comment Objects. Track these comments through the git history.
3. Build an algorithm that computes each comments' health score based on the metrics defined in the original one pager.
4. Build a light IDE plugin that will highlight comments according to their health rating (invoked via an IDE command)