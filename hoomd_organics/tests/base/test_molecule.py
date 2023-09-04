import pytest

from hoomd_organics import CoPolymer, Molecule, Polymer
from hoomd_organics.tests import BaseTest
from hoomd_organics.utils import FF_Types, exceptions


class TestMolecule(BaseTest):
    def test_molecule_from_mb_compound(self, benzene_mb):
        molecule = Molecule(num_mols=2, compound=benzene_mb)
        assert len(molecule.molecules) == 2

    def test_molecule_from_gmso_topology(self, benzene_gmso):
        molecule = Molecule(num_mols=2, compound=benzene_gmso)
        assert len(molecule.molecules) == 2

    def test_molecule_from_smiles(self, benzene_smiles):
        molecule = Molecule(num_mols=2, smiles=benzene_smiles)
        assert len(molecule.molecules) == 2

    def test_molecule_from_file(self, benzene_mol2):
        molecule = Molecule(num_mols=2, file=benzene_mol2)
        assert len(molecule.molecules) == 2

    def test_molecule_topology_benzene(self, benzene_mb):
        molecule = Molecule(num_mols=2, compound=benzene_mb)
        assert set(molecule.topology_information["particle_types"]) == {
            "C",
            "H",
        }
        assert set(molecule.topology_information["pair_types"]) == {
            ("C", "C"),
            ("C", "H"),
            ("H", "H"),
        }
        assert len(set(molecule.topology_information["particle_typeid"])) == 2
        assert len(molecule.topology_information["bond_types"]) == 2
        assert len(molecule.topology_information["angle_types"]) == 2
        assert len(molecule.topology_information["dihedral_types"]) == 3
        assert not any(molecule.topology_information["particle_charge"])

    def test_validate_force_field_oplsaa(self, benzene_mb):
        molecule = Molecule(
            num_mols=2, force_field="oplsaa", compound=benzene_mb
        )
        assert molecule.ff_type == FF_Types.oplsaa
        assert set(molecule.topology_information["particle_types"]) == {
            "opls_145",
            "opls_146",
        }
        assert any(molecule.topology_information["particle_charge"])

    def test_validate_force_field_xml_file(self, benzene_mb):
        molecule = Molecule(
            num_mols=2, force_field="oplsaa.xml", compound=benzene_mb
        )
        assert molecule.ff_type == FF_Types.oplsaa
        assert set(molecule.topology_information["particle_types"]) == {
            "opls_145",
            "opls_146",
        }
        assert any(molecule.topology_information["particle_charge"])

    def test_validate_force_field_xml_file_path(self, benzene_mb, benzene_xml):
        molecule = Molecule(
            num_mols=2, force_field=benzene_xml, compound=benzene_mb
        )
        assert molecule.ff_type == FF_Types.custom
        assert set(molecule.topology_information["particle_types"]) == {
            "opls_145",
            "opls_146",
        }
        assert any(molecule.topology_information["particle_charge"])

    def test_validate_force_field_not_xml_file(self, benzene_mb):
        with pytest.raises(ValueError):
            Molecule(num_mols=2, force_field="oplsaa.txt", compound=benzene_mb)

    def test_validate_force_field_not_supported(self, benzene_mb):
        with pytest.raises(ValueError):
            Molecule(num_mols=2, force_field="oplsaa2", compound=benzene_mb)

    def test_validate_force_field_invalid_xml_file(self, benzene_mb):
        with pytest.raises(ValueError):
            Molecule(num_mols=2, force_field="oplsaa2.xml", compound=benzene_mb)

    def test_validate_force_field_hoomd_ff_aa(
        self, benzene_mb, benzene_hoomd_ff
    ):
        hoomd_ff = benzene_hoomd_ff(include_hydrogen=True)
        molecule = Molecule(
            num_mols=2, force_field=hoomd_ff, compound=benzene_mb
        )
        assert molecule.ff_type == FF_Types.Hoomd

    def test_validate_fore_field_hoomd_ff_ua(
        self, benzene_mb, benzene_hoomd_ff
    ):
        hoomd_ff = benzene_hoomd_ff(include_hydrogen=False)
        molecule = Molecule(
            num_mols=2, force_field=hoomd_ff, compound=benzene_mb
        )
        assert molecule.ff_type == FF_Types.Hoomd

    def test_validate_force_field_hoomd_ff_missing_pair(
        self, benzene_mb, benzene_hoomd_ff
    ):
        hoomd_ff = benzene_hoomd_ff(include_hydrogen=True)
        hoomd_ff.pop(0)
        with pytest.raises(exceptions.MissingPairPotentialError):
            Molecule(num_mols=2, force_field=hoomd_ff, compound=benzene_mb)

    def test_validate_force_field_hoomd_ff_missing_bond(
        self, benzene_mb, benzene_hoomd_ff
    ):
        hoomd_ff = benzene_hoomd_ff(include_hydrogen=True)
        hoomd_ff.pop(1)
        with pytest.raises(exceptions.MissingBondPotentialError):
            Molecule(num_mols=2, force_field=hoomd_ff, compound=benzene_mb)

    def test_validate_force_field_hoomd_ff_invalid_pair(
        self, benzene_mb, benzene_hoomd_ff
    ):
        hoomd_ff = benzene_hoomd_ff(include_hydrogen=True, invalid_pair=True)
        with pytest.raises(exceptions.MissingPairPotentialError):
            Molecule(num_mols=2, force_field=hoomd_ff, compound=benzene_mb)

    def test_validate_force_field_hoomd_ff_missing_Coulomb(
        self, benzene_mb, benzene_xml, benzene_hoomd_ff
    ):
        hoomd_ff = benzene_hoomd_ff(include_hydrogen=True)
        typed_molecule = Molecule(
            num_mols=2, force_field=benzene_xml, compound=benzene_mb
        )
        with pytest.raises(exceptions.MissingCoulombPotentialError):
            Molecule(
                num_mols=2,
                force_field=hoomd_ff,
                compound=typed_molecule.gmso_molecule,
            )

    def test_coarse_grain_with_single_beads(self, benzene_smiles):
        molecule = Molecule(num_mols=2, smiles=benzene_smiles)
        molecule.coarse_grain(beads={"A": benzene_smiles})
        assert molecule.topology_information["particle_types"] == ["A"]
        assert molecule.n_particles == 2
        assert molecule.n_bonds == 0

    def test_coarse_grain_with_multiple_single_beads(
        self, octane_smiles, ethane_smiles
    ):
        molecule = Molecule(num_mols=2, smiles=octane_smiles)
        molecule.coarse_grain(beads={"A": ethane_smiles})
        assert molecule.molecules[0].n_particles == 4
        assert molecule.topology_information["bond_types"] == {("A", "A")}

    def test_coarse_grain_with_different_beads(
        self, pps_smiles, benzene_smiles
    ):
        molecule = Molecule(num_mols=2, smiles=pps_smiles)
        molecule.coarse_grain(beads={"A": benzene_smiles, "B": "S"})
        assert molecule.molecules[0].n_particles == 2
        assert molecule.topology_information["particle_types"] == ["A", "B"]
        assert molecule.topology_information["bond_types"] == {("A", "B")}

    def test_coarse_grain_invalid_beads(self, benzene_smiles):
        molecule = Molecule(num_mols=2, smiles=benzene_smiles)
        with pytest.raises(ValueError):
            molecule.coarse_grain(beads={"A": "CO"})


class TestPolymer(BaseTest):
    def test_polymer(self, dimethylether_smiles):
        polymer = Polymer(
            lengths=3,
            num_mols=1,
            smiles=dimethylether_smiles,
            bond_indices=[3, -1],
            bond_length=0.15,
            bond_orientation=[None, None],
        )
        assert polymer.n_particles == 23
        assert polymer.n_bonds == 22
        assert ("O", "C", "C") in polymer.topology_information["angle_types"]
        assert ("O", "C", "C", "O") in polymer.topology_information[
            "dihedral_types"
        ]

    def test_polymer_different_chain_lengths(self, dimethylether_smiles):
        polymer = Polymer(
            lengths=[3, 4],
            num_mols=[1, 1],
            smiles=dimethylether_smiles,
            bond_indices=[3, -1],
            bond_length=0.15,
            bond_orientation=[None, None],
        )
        assert polymer.n_particles == 53
        assert len(polymer.molecules[0].labels["monomer"]) == 3
        assert len(polymer.molecules[1].labels["monomer"]) == 4

    def test_polymer_different_num_mol(self, dimethylether_smiles):
        polymer = Polymer(
            lengths=[3, 2],
            num_mols=[1, 2],
            smiles=dimethylether_smiles,
            bond_indices=[3, -1],
            bond_length=0.15,
            bond_orientation=[None, None],
        )
        assert polymer.n_particles == 55
        assert len(polymer.molecules[0].labels["monomer"]) == 3
        assert len(polymer.molecules[1].labels["monomer"]) == 2
        assert len(polymer.molecules[2].labels["monomer"]) == 2

    def test_polymer_unequal_num_mol_length(self, dimethylether_smiles):
        with pytest.raises(ValueError):
            Polymer(
                lengths=[3],
                num_mols=[1, 2],
                smiles=dimethylether_smiles,
                bond_indices=[3, -1],
                bond_length=0.15,
                bond_orientation=[None, None],
            )


class TestCopolymer(BaseTest):
    def test_copolymer_with_sequence(self, polyethylene, polyDME):
        copolymer = CoPolymer(
            monomer_A=polyDME,
            monomer_B=polyethylene,
            lengths=1,
            num_mols=1,
            sequence="ABA",
        )
        assert copolymer.n_particles == 22
        assert ("C", "C", "C", "C") in copolymer.topology_information[
            "dihedral_types"
        ]

    def test_copolymer_with_sequence_different_chain_lengths(
        self, polyethylene, polyDME
    ):
        copolymer = CoPolymer(
            monomer_A=polyDME,
            monomer_B=polyethylene,
            lengths=[2, 3],
            num_mols=[1, 1],
            sequence="ABA",
        )

        assert copolymer.molecules[0].n_particles == 42
        assert copolymer.molecules[1].n_particles == 62

    def test_copolymer_with_sequence_different_num_mol(
        self, polyethylene, polyDME
    ):
        copolymer = CoPolymer(
            monomer_A=polyDME,
            monomer_B=polyethylene,
            lengths=[2, 3],
            num_mols=[1, 2],
            sequence="ABA",
        )

        assert copolymer.molecules[0].n_particles == 42
        assert copolymer.molecules[1].n_particles == 62
        assert copolymer.molecules[2].n_particles == 62

    def test_copolymer_random_sequence(self, polyethylene, polyDME):
        copolymer = CoPolymer(
            monomer_A=polyDME,
            monomer_B=polyethylene,
            lengths=[3],
            num_mols=[1],
            random_sequence=True,
            seed=42,
        )
        # sequence is BAA
        assert copolymer.n_particles == 22
        assert ("O", "C", "C", "O") in copolymer.topology_information[
            "dihedral_types"
        ]
