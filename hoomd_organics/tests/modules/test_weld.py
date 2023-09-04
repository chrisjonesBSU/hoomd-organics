import os

import gsd.hoomd
import hoomd

from hoomd_organics import Simulation
from hoomd_organics.modules.utils import add_void_particles
from hoomd_organics.modules.welding import Interface, SlabSimulation
from hoomd_organics.tests.base_test import BaseTest


class TestWelding(BaseTest):
    def test_interface(self, polyethylene_system):
        sim = Simulation(
            initial_state=polyethylene_system.hoomd_snapshot,
            forcefield=polyethylene_system.hoomd_forcefield,
            log_write_freq=2000,
        )
        sim.add_walls(wall_axis=(1, 0, 0), sigma=1, epsilon=1, r_cut=2)
        sim.run_update_volume(
            n_steps=1000,
            period=10,
            kT=2.0,
            tau_kt=0.01,
            final_box_lengths=sim.box_lengths / 2,
        )
        sim.save_restart_gsd()
        interface = Interface(
            gsd_file="restart.gsd", interface_axis="x", gap=0.1
        )
        interface_snap = interface.hoomd_snapshot
        with gsd.hoomd.open("restart.gsd", "rb") as traj:
            slab_snap = traj[0]

        assert interface_snap.particles.N == slab_snap.particles.N * 2
        assert interface_snap.bonds.N == slab_snap.bonds.N * 2
        assert interface_snap.bonds.M == slab_snap.bonds.M
        assert interface_snap.angles.N == slab_snap.angles.N * 2
        assert interface_snap.angles.M == slab_snap.angles.M
        assert interface_snap.dihedrals.N == slab_snap.dihedrals.N * 2
        assert interface_snap.dihedrals.M == slab_snap.dihedrals.M
        assert interface_snap.pairs.N == slab_snap.pairs.N * 2
        assert interface_snap.pairs.M == slab_snap.pairs.M

        if os.path.isfile("restart.gsd"):
            os.remove("restart.gsd")

    def test_slab_sim_xaxis(self, polyethylene_system):
        sim = SlabSimulation(
            initial_state=polyethylene_system.hoomd_snapshot,
            forcefield=polyethylene_system.hoomd_forcefield,
            log_write_freq=2000,
        )
        assert sim._axis_array == (1, 0, 0)
        assert sim._axis_index == 0
        sim.run_NVT(kT=1.0, tau_kt=0.01, n_steps=500)

    def test_slab_sim_yaxis(self, polyethylene_system):
        sim = SlabSimulation(
            initial_state=polyethylene_system.hoomd_snapshot,
            forcefield=polyethylene_system.hoomd_forcefield,
            interface_axis="y",
            log_write_freq=2000,
        )
        assert sim._axis_array == (0, 1, 0)
        assert sim._axis_index == 1
        sim.run_NVT(kT=1.0, tau_kt=0.01, n_steps=500)

    def test_slab_sim_zaxis(self, polyethylene_system):
        sim = SlabSimulation(
            initial_state=polyethylene_system.hoomd_snapshot,
            forcefield=polyethylene_system.hoomd_forcefield,
            interface_axis="z",
            log_write_freq=2000,
        )
        assert sim._axis_array == (0, 0, 1)
        assert sim._axis_index == 2
        sim.run_NVT(kT=1.0, tau_kt=0.01, n_steps=500)

    def test_weld_sim(self, polyethylene_system):
        sim = SlabSimulation(
            initial_state=polyethylene_system.hoomd_snapshot,
            forcefield=polyethylene_system.hoomd_forcefield,
            log_write_freq=2000,
        )
        sim.run_NVT(kT=1.0, tau_kt=0.01, n_steps=500)
        sim.save_restart_gsd()
        # Create interface system from slab restart.gsd file
        interface = Interface(
            gsd_file="restart.gsd", interface_axis="x", gap=0.1
        )
        sim = SlabSimulation(
            initial_state=interface.hoomd_snapshot,
            forcefield=polyethylene_system.hoomd_forcefield,
        )
        if os.path.isfile("restart.gsd"):
            os.remove("restart.gsd")

    def test_void_particle(self, polyethylene_system):
        init_snap = polyethylene_system.hoomd_snapshot
        init_num_particles = init_snap.particles.N
        init_types = init_snap.particles.types
        void_snap, ff = add_void_particles(
            init_snap,
            polyethylene_system.hoomd_forcefield,
            void_diameter=0.4,
            num_voids=1,
            void_axis=(1, 0, 0),
            epsilon=1,
            r_cut=0.4,
        )
        assert init_num_particles == void_snap.particles.N - 1
        lj = [i for i in ff if isinstance(i, hoomd.md.pair.LJ)][0]
        for p_type in init_types:
            assert lj.params[(p_type, "VOID")]["sigma"] == 0.4
            assert lj.params[(p_type, "VOID")]["epsilon"] == 1
