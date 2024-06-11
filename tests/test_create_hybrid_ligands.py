from ligate.awh.pipeline.create_hybrid_ligands import CreateHybridLigandsParams, \
    create_hybrid_ligands


def test_create_hybrid_ligands(tmp_path, data_dir):
    params = CreateHybridLigandsParams(
        directory=data_dir / "awh" / "1" / "create-hybrid-ligands" / "input",
        cores=4
    )
    create_hybrid_ligands(params)
