import random
import pytest
from app.simulators.boolean import minimize
from app.simulators.clock import Counter, PulseDivider, SquareDivider, TrafficLight, bits_for_cycles


def test_all_three_variable_functions_and_random_four():
    for mask in range(256):
        on = [n for n in range(8) if mask & (1 << n)]
        result = minimize(on, ("A", "B", "C"))
        assert [result.evaluate(n) for n in range(8)] == [int(n in on) for n in range(8)]
    rng = random.Random(1701)
    for _ in range(120):
        on = [n for n in range(16) if rng.randrange(2)]
        result = minimize(on)
        assert [result.evaluate(n) for n in range(16)] == [int(n in on) for n in range(16)]


def test_minimal_known_cover_and_dont_cares():
    result = minimize([0, 1, 2, 3])
    assert result.terms == ("00--",)
    assert minimize([]).expression() == "0"
    assert minimize(range(16)).expression() == "1"
    result = minimize([1, 3], ("A", "B", "C"), [5, 7])
    assert result.terms == ("--1",)
    with pytest.raises(ValueError):
        minimize([1], dont_cares=[1])



@pytest.mark.parametrize("cycles,bits", [(1,1), (2,1), (3,2), (4096,12), (5208,13), (50000000,26)])
def test_width(cycles, bits):
    assert bits_for_cycles(cycles) == bits


def test_counter_boundary_and_large_jump():
    counter = Counter(5208)
    assert counter.advance(5207) == 0
    assert counter.value == 5207
    assert counter.advance() == 1 and counter.value == 0
    assert counter.advance(5208 * 1000000 + 7) == 1000000
    assert counter.value == 7
    counter.reset(); assert counter.value == 0
    with pytest.raises(ValueError): counter.advance(-1)


def test_pulse_and_square_are_different():
    pulse, square = PulseDivider(4), SquareDivider(2)
    p, s = [], []
    for _ in range(8):
        pulse.advance(); square.advance()
        p.append(pulse.pulse); s.append(square.output)
    assert p == [0,0,0,1,0,0,0,1]
    assert s == [0,1,1,0,0,1,1,0]
    pulse.reset(); square.reset()
    assert pulse.pulse == square.output == 0
    single = PulseDivider(1)
    single.advance(); assert single.pulse == 1


def test_traffic_boundaries_reset_and_fast_equivalence():
    slow = TrafficLight(3, 2, 1, 4)
    assert slow.state == "ROJO"
    slow.advance(11); assert slow.state == "ROJO"
    slow.advance(); assert slow.state == "VERDE"
    slow.advance(8); assert slow.state == "AMARILLO"
    slow.advance(4); assert slow.state == "ROJO"
    fast = TrafficLight(3, 2, 1, 4)
    fast.advance(3001)
    slow.reset()
    for _ in range(3001): slow.advance()
    assert fast.state == slow.state
    assert fast.ticks == slow.ticks
    assert fast.divider.counter.value == slow.divider.counter.value
    assert sum(fast.outputs.values()) == 1
    fast.reset(); assert fast.state == "ROJO" and fast.cycles == 0


@pytest.mark.parametrize("bad", [0, -2, 1.2, True])
def test_invalid_counter_parameters(bad):
    with pytest.raises(ValueError): Counter(bad)
    with pytest.raises(ValueError): TrafficLight(red=bad)


def test_configurable_hdl_defaults():
    from app.core.examples import clock_project
    p = clock_project(red=7, green=8, yellow=3, clock_hz=1000, period=100, half_period=25, modulus=13)
    assert 'CLOCK_HZ=1000' in p.files['traffic_light.v']
    assert 'RED_SECONDS=7' in p.files['traffic_light.v']
    assert 'CYCLES=100' in p.files['pulse_generator.v']
    assert 'HALF_CYCLES=25' in p.files['square_divider.v']
    assert 'MODULUS=13' in p.files['modulo_counter.v']

