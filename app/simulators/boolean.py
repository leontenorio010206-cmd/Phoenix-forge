"""Exact Quine-McCluskey minimization for up to six variables.

Prime implicants followed by an exact covering search (terms, then literals).
Don't-care rows may participate in merging but never require covering.
"""
from dataclasses import dataclass


def matches(pattern, value):
    bits = format(value, "0%db" % len(pattern))
    return all(a == "-" or a == b for a, b in zip(pattern, bits))


@dataclass(frozen=True)
class Reduction:
    variables: tuple
    minterms: tuple
    primes: tuple
    terms: tuple

    def evaluate(self, value):
        return int(any(matches(p, value) for p in self.terms))

    def expression(self, verilog=False):
        if not self.terms:
            return "1'b0" if verilog else "0"
        rendered = []
        for term in self.terms:
            bits = [("~" if verilog else "¬") + var if bit == "0" else var
                    for var, bit in zip(self.variables, term) if bit != "-"]
            if not bits:
                return "1'b1" if verilog else "1"
            rendered.append("(" + (" & " if verilog else " · ").join(bits) + ")")
        return (" | " if verilog else " + ").join(rendered)


def minimize(minterms, variables=("A", "B", "C", "D"), dont_cares=()):
    variables = tuple(variables)
    n = len(variables)
    if not 1 <= n <= 6 or len(set(variables)) != n:
        raise ValueError("Se admiten de 1 a 6 variables distintas")
    on, dc = set(minterms), set(dont_cares)
    if on & dc or any(type(i) is not int or not 0 <= i < (1 << n) for i in on | dc):
        raise ValueError("Minitérminos inválidos")
    current = {format(i, "0%db" % n) for i in on | dc}
    primes = set()
    while current:
        used, following = set(), set()
        for a in sorted(current):
            for b in sorted(current):
                if a >= b or [i for i, x in enumerate(a) if x == "-"] != [i for i, x in enumerate(b) if x == "-"]:
                    continue
                differences = [i for i in range(n) if a[i] != b[i]]
                if len(differences) == 1:
                    i = differences[0]
                    following.add(a[:i] + "-" + a[i + 1:])
                    used.update((a, b))
        primes.update(current - used)
        current = following
    primes = sorted(p for p in primes if any(matches(p, i) for i in on))
    covers = {p: {i for i in on if matches(p, i)} for p in primes}
    candidates = {i: [p for p in primes if i in covers[p]] for i in on}
    essentials = {items[0] for items in candidates.values() if len(items) == 1}
    remaining = on - set().union(set(), *(covers[p] for p in essentials))
    best = None

    def cost(terms):
        return len(terms), sum(n - p.count("-") for p in terms), tuple(sorted(terms))

    def cover(left, selected):
        nonlocal best
        if not left:
            if best is None or cost(selected) < cost(best):
                best = set(selected)
            return
        if best is not None and len(selected) >= len(best):
            return
        row = min(left, key=lambda i: (len(candidates[i]), i))
        for p in candidates[row]:
            cover(left - covers[p], selected | {p})

    cover(remaining, essentials)
    return Reduction(variables, tuple(sorted(on)), tuple(primes), tuple(sorted(best or ())))

