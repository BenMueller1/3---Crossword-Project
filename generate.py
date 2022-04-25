import sys
import pdb
from crossword import *
from collections import deque

class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        breakpoint()  # remove this before submitting
        #self.revise(list(self.crossword.variables)[0], list(self.crossword.variables)[2])  # remove this before submitting
        self.ac3()
        breakpoint()   # remove before submitting
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for var, domain in self.domains.items():
            correct_length = var.length
            new_domain = set()
            for word in domain:
                if len(word) == correct_length:
                    new_domain.add(word)
            self.domains[var] = new_domain


    def check_if_y_has_value_satisfying_constraint(self, x, x_val, y):
        for y_val in self.domains[y]:
            # if this y_val satisfies the constraints when x=x_val, we return True
            intersection = self.crossword.overlaps[x, y]
            if intersection == None:
                return True
            if x_val[intersection[0]] == y_val[intersection[1]]:
                return True
        return False

        
    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.

        Recall: A is arc consistent with B if no matter what value A takes on, B still has a possible value
        """
        revised = False
        new_domain = set()
        for x_val in self.domains[x]:
            # if no y_val in Y's domain satisfies constraint for (X,Y), delete x_val from X.domain and set revise = True
            if not self.check_if_y_has_value_satisfying_constraint(x, x_val, y):  # ie if y doesn't have a value satisfying the constraints when x=x_val
                revised = True
            else:
                new_domain.add(x_val)
        self.domains[x] = new_domain
        return revised


    def get_all_arcs(self):
        """
        Returns set of all variables that have overlaps (because these are the ones that have constraints between them)
        """
        # using sets allows us to ensure we don't add in duplicate sets
        arcs = []
        for var in self.domains.keys():
            for neighbor in self.crossword.neighbors(var):
                arc = set([var, neighbor])
                if arc not in arcs:
                    arcs.append(arc)
        
        # now change every set in arcs to a tuple (so that we can index them)
        arcs_as_tuples = []
        for arc in arcs:
            arcs_as_tuples.append(tuple(arc))

        return arcs_as_tuples


    def ac3(self, arcs=None):
        """

        TODO I DO NOT THINK THIS IS WORKING

        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        # need to fill a queue with every arc in the CSP (if arcs==None initially)
        if arcs == None:
            arcs = self.get_all_arcs()
        
        queue = deque(list(arcs))  # Use appendleft() and pop() for this to be treated like a queue
        while queue: # while queue is nonempty
            arc = queue.pop()
            if self.revise(arc[0], arc[1]):
                if len(self.domains[arc[0]]):
                    return False
                for neighbor in self.crossword.neighbors[arc[0]]:
                    if neighbor is not arc[1]:
                        new_arc = set([neighbor, arc[0]])
                        queue.appendleft(new_arc)
        return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        for key, value in assignment.items():
            if value == None:
                return False
        return True

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        # check that all values in assignment are distinct
        unique_checker = set()
        for key, value in assignment.items():
            if value != None:
                if value in unique_checker:
                    return False    # returns false if there is a duplicate
                else:
                    b = unique_checker.add(value)

        # check that all values are the correect length (ie node consistent)
        

        # check no conflicts between neighboring variables (ie arc consistent)



    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        raise NotImplementedError

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        raise NotImplementedError

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        raise NotImplementedError


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
