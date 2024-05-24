from ligate.awh.pipeline.create_hybrid_ligands import CreateHybridLigandsParams, \
    create_hybrid_ligands


def test_create_hybrid_ligands(gmx, tmp_path, data_dir):
    params = CreateHybridLigandsParams(
        input_dir=data_dir / "awh" / "1" / "create-hybrid-ligands" / "input",
        output_dir=tmp_path,
        cores=4
    )
    create_hybrid_ligands(params, gmx=gmx)
