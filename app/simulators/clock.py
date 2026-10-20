"""Integer event-driven simulation: no loops over 50 million input cycles."""
from dataclasses import dataclass

REFERENCE_HZ = 50_000_000


def positive_int(value):
    if type(value) is not int or not 1 <= value <= 2 ** 63 - 1:
        raise ValueError("Se requiere un entero positivo de hasta 63 bits")
    return value


def bits_for_cycles(cycles):
    return max(1, (positive_int(cycles) - 1).bit_length())


def valid_step(cycles):
    if type(cycles) is not int or cycles < 0:
        raise ValueError("El número de ciclos no puede ser negativo")


@dataclass
class Counter:
    modulus: int
    value: int = 0

    def __post_init__(self):
        positive_int(self.modulus)
        if type(self.value) is not int or not 0 <= self.value < self.modulus:
            raise ValueError("Valor de contador fuera de rango")

    def advance(self, cycles=1):
        valid_step(cycles)
        wraps, self.value = divmod(self.value + cycles, self.modulus)
        return wraps

    def reset(self):
        self.value = 0


class PulseDivider:
    def __init__(self, period=REFERENCE_HZ):
        self.counter = Counter(period)
        self.pulse = 0

    @property
    def period(self):
        return self.counter.modulus

    def advance(self, cycles=1):
        wraps = self.counter.advance(cycles)
        if cycles:
            self.pulse = int(self.counter.value == 0)
        return wraps

    def reset(self):
        self.counter.reset()
        self.pulse = 0


class SquareDivider:
    def __init__(self, half_period=REFERENCE_HZ // 2):
        self.counter = Counter(half_period)
        self.output = 0

    def advance(self, cycles=1):
        edges = self.counter.advance(cycles)
        self.output ^= edges % 2
        return edges

    def reset(self):
        self.counter.reset()
        self.output = 0


class TrafficLight:
    """Added design: red -> green -> yellow, defaults 5/5/2 seconds.

    The PDF does not prescribe order, durations, active polarity or reset.
    State changes on the same rising edge as divider rollover.
    """
    STATES = ("ROJO", "VERDE", "AMARILLO")

    def __init__(self, red=5, green=5, yellow=2, clock_hz=REFERENCE_HZ):
        self.durations = tuple(positive_int(v) for v in (red, green, yellow))
        self.clock_hz = positive_int(clock_hz)
        self.divider = PulseDivider(clock_hz)
        self.ticks = 0
        self.cycles = 0

    def advance(self, cycles=1):
        ticks = self.divider.advance(cycles)
        self.cycles += cycles
        self.ticks += ticks
        return self.outputs

    @property
    def state(self):
        pos = self.ticks % sum(self.durations)
        for name, duration in zip(self.STATES, self.durations):
            if pos < duration:
                return name
            pos -= duration

    @property
    def outputs(self):
        return {name: int(name == self.state) for name in self.STATES}

    def reset(self):
        self.divider.reset()
        self.ticks = self.cycles = 0

