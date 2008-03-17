import py
from pypy.rpython.memory.simulator import MemoryBlock, MemorySimulator
from pypy.rpython.memory.simulator import MemorySimulatorError
from pypy.rpython.memory import simulator

import struct

class TestMemoryBlock(object):
    def test_getsetbyte(self):
        block = MemoryBlock(1, 100)
        block.setbytes(1, "hello")
        assert block.getbytes(1, 5) == "hello"
        #uninitialized memory:
        py.test.raises(MemorySimulatorError, block.getbytes, 2, 5)
        #access over block borders:
        py.test.raises(MemorySimulatorError, block.setbytes, 98, "long string")
        #accessing freed memory:
        block.free()
        py.test.raises(MemorySimulatorError, block.getbytes, 2, 5)
        #freeing free block:
        py.test.raises(MemorySimulatorError, block.getbytes, 2, 5)

class TestMemorySimulator(object):
    def test_find_block(self):
        simulator = MemorySimulator()
        for size in [100, 100, 200, 300, 100, 50]:
            simulator.malloc(size)
        for address in [12, 99, 110, 190, 210, 310, 420, 450, 510, 630, 710]:
            block = simulator.find_block(address)
            assert block.baseaddress <= address < block.baseaddress + block.size

    def test_malloc(self):
        simulator = MemorySimulator()
        for size in [2, 4, 8, 16, 32, 64, 128]:
            baseaddress = simulator.malloc(size)
            block = simulator.find_block(baseaddress)
            assert block.size == size

    def test_set_get_struct(self):
        simulator = MemorySimulator()
        address = simulator.malloc(100)
        simulator.setstruct("iic", address, 1, 2, "a")
        assert simulator.getstruct("iic", address) == (1, 2, "a")

    def test_free(self):
        simulator = MemorySimulator()
        addr = simulator.malloc(100)
        simulator.free(addr)
        py.test.raises(MemorySimulatorError, simulator.free, addr)
        py.test.raises(MemorySimulatorError, simulator.free, 0)

    def test_memcopy(self):
        simulator = MemorySimulator()
        addr1 = simulator.malloc(1000)
        addr2 = simulator.malloc(500)
        simulator.setstruct("iii", addr1, 1, 2, 3)
        simulator.memcopy(addr1, addr1 + 500, struct.calcsize("iii"))
        simulator.memcopy(addr1 + 500, addr2, struct.calcsize("iii"))
        assert simulator.getstruct("iii", addr1) == (1, 2, 3)
        assert simulator.getstruct("iii", addr1 + 500) == (1, 2, 3)
        assert simulator.getstruct("iii", addr2) == (1, 2, 3)

    def test_out_of_memory(self):
        sim = MemorySimulator(1 * 1024 * 1024)
        def f():
            for i in xrange(10000):
                sim.malloc(4096)
        py.test.raises(MemorySimulatorError, f)
        sim = MemorySimulator(1 * 1024 * 1024)
        def g():
            for i in xrange(10000):
                sim.free(sim.malloc(4096))
        g() #does not raise

    def test_object_access(self):
        sim = MemorySimulator()
        def f(x):
            return x + 1
        def g(x):
            return x + 2
        a1 = sim.get_address_of_object(f)
        a2 = sim.get_address_of_object(g)
        assert sim.get_py_object(a1)(1) == 2
        assert sim.get_py_object(a2)(1) == 3
    
