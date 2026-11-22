#!/usr/bin/env python3
"""Compare named feature holders and tags and ordered world mutations with pinned vanilla."""
import argparse
import json
import os
from pathlib import Path
import platform
import random
import subprocess
try:
    from . import lab,test_rust_parity as base
except ImportError:
    import lab
    import test_rust_parity as base


def catalog():
    encode=lambda value:json.dumps(value,separators=(',',':'))
    features={'apex:no_op':{'type':'no_op'},'apex:island':{'type':'end_island'},'apex:platform':{'type':'end_platform'},'apex:void':{'type':'void_start_platform'},'minecraft:noop':{'type':'no_op'}}
    features['apex:fill']={'type':'fill_layer','height':1,'state':{'id':'oak_log','properties':{'axis':'x'}}}
    features['apex:replace']={'type':'replace_single_block','targets':[{'target':{'predicate_type':'random_block_match','block':'stone','probability':0.5},'state':'gold_ore'},{'target':{'predicate_type':'block_match','block':'oak_log'},'state':{'id':'water','properties':{'level':'1'}}}]}
    features['apex:scatter']={'type':'scattered_ore','targets':[{'target':{'predicate_type':'block_match','block':'stone'},'state':'iron_ore'}],'size':8,'discard_chance_on_air_exposure':0.5}
    placed={
        'apex:a_noop':{'feature':'apex:no_op','placement':[]},
        'apex:b_false':{'feature':'apex:no_op','placement':[{'type':'count','count':0}]},
        'apex:c_island':{'feature':'apex:island','placement':[{'type':'in_square'}]},
        'apex:d_platform':{'feature':'apex:platform','placement':[{'type':'offset','x':1,'y':2,'z':-1}]},
        'apex:e_nested':{'feature':{'type':'simple_random_selector','features':['apex:c_island','apex:d_platform','apex:b_false']},'placement':[{'type':'count','count':2}]},
        'minecraft:noop':{'feature':'minecraft:noop','placement':[]},
        'apex:h_scatter':{'feature':'apex:scatter','placement':[]},
        'apex:f_fill':{'feature':'apex:fill','placement':[{'type':'in_square'}]},
        'apex:g_replace':{'feature':'apex:replace','placement':[{'type':'count','count':2},{'type':'in_square'},{'type':'height_range','height':{'absolute':-63}}]},
    }
    placed['apex:i_filtered']={'feature':'apex:replace','placement':[{'type':'count','count':3},{'type':'block_predicate_filter','predicate':{'type':'matching_blocks','blocks':['stone','oak_log']}}]}
    placed['apex:j_scan']={'feature':'apex:replace','placement':[{'type':'environment_scan','direction_of_search':'down','target_condition':{'type':'matching_blocks','blocks':'stone'},'allowed_search_condition':{'type':'not','predicate':{'type':'matching_blocks','blocks':'obsidian'}},'max_steps':8}]}
    placed['apex:k_volume']={'feature':'apex:no_op','placement':[{'type':'block_predicate_filter','predicate':{'type':'volume_match','min':[-1,0,-1],'max':[1,1,1],'match':{'type':'not','predicate':{'type':'matching_blocks','blocks':'air'}}}}]}
    placed['apex:l_fluids']={'feature':{'type':'replace_single_block','targets':[{'target':{'predicate_type':'block_match','block':'water'},'state':'stone'}]},'placement':[{'type':'count','count':3},{'type':'block_predicate_filter','predicate':{'type':'matching_fluids','fluids':['flowing_water']}}]}
    placed['apex:m_fluid_sequence']={'feature':{'type':'sequence','features':[{'feature':{'type':'fill_layer','height':128,'state':{'id':'water','properties':{'level':'1'}}},'placement':[]},'apex:l_fluids']},'placement':[]}
    tags={
        'apex:nonempty':{'values':['apex:a_noop','apex:c_island','apex:d_platform','apex:c_island']},
        'apex:empty':{'values':[]},
        'apex:nested':{'values':['#apex:nonempty','apex:e_nested','apex:f_fill','apex:g_replace','apex:h_scatter','apex:i_filtered','apex:j_scan','apex:k_volume','apex:m_fluid_sequence']},
        'apex:optional':{'values':[{'id':'apex:missing','required':False},'apex:a_noop']},
        'apex:invalid':{'values':['apex:missing']},
    }
    features['apex:overlay']={'type':'overlay','features':[{'feature':{'type':'no_op'},'placement':[{'type':'count','count':0}]},{'feature':{'type':'end_island'},'placement':[{'type':'in_square'}]},{'feature':{'type':'end_platform'},'placement':[]}]}
    placed['apex:n_overlay']={'feature':'apex:overlay','placement':[{'type':'count','count':2}]}
    features['apex:composite']={'type':'sequence','features':'#apex:nested'}
    return {key:{name:encode(value) for name,value in values.items()} for key,values in [('features',features),('placed',placed),('tags',tags)]}


def definitions():
    inline={'feature':'apex:island','placement':[]}
    for root in [*catalog()['features'],'noop',':noop','apex:missing','#apex:no_op','APEX:no_op',None,False,[]]:yield False,root
    for root in [*catalog()['placed'],'noop',':noop','apex:missing','#apex:nonempty',inline,{'feature':'apex:composite','placement':[{'type':'count','count':2}]}]:yield True,root
    for values in ['apex:c_island','#apex:nonempty','#apex:empty','#apex:nested','#apex:optional','#apex:invalid','#apex:missing',[],['apex:c_island','apex:c_island'],['apex:a_noop','apex:b_false','apex:c_island'],['apex:c_island',inline],[inline,'apex:c_island'],inline]:
        for kind in ['sequence','overlay','simple_random_selector']:yield False,{'type':kind,'features':values}
    for name in ['apex:e_nested','apex:b_false','apex:missing']:
        yield False,{'type':'random_boolean_selector','feature_true':name,'feature_false':inline}
        yield False,{'type':'random_selector','features':[{'feature':name,'chance':0.5}],'default':'apex:d_platform'}
        yield False,{'type':'weighted_random_selector','features':[{'data':name,'weight':0},{'data':'apex:d_platform','weight':1}]}
    for blocks in [[],['stone','stone','water'],['missing'],'missing','#missing',['#tag'],None]:
        yield True,{'feature':'apex:replace','placement':[{'type':'block_predicate_filter','predicate':{'type':'matching_blocks','blocks':blocks}}]}
    for fluids in ['empty','water','flowing_water','lava',[],['water','flowing_water'],'missing','#missing',['#water'],None]:
        yield True,{'feature':'apex:replace','placement':[{'type':'block_predicate_filter','predicate':{'type':'matching_fluids','fluids':fluids}}]}


def corpus():
    for legacy in [False,True]:
        for seed in [0,-1,0x123456789abcdef]:
            for placed,definition in definitions():
                for fail in [-1,0,7]:
                    for reject in [0,3]:
                        for worldgen in [False,True]:
                            yield {'worldgen':worldgen,'definition':json.dumps(definition,separators=(',',':')),'placed_root':placed,'origin':[15,64,15],'legacy':legacy,'seed':seed,'reject':reject,'fail':fail,'repeats':2}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--prepare",action="store_true");args=parser.parse_args()
    build=lab.LOCAL/"rust-feature-catalog-parity";build.mkdir(parents=True,exist_ok=True)
    report_path=build/"report.json";report_path.unlink(missing_ok=True)
    if args.prepare:lab.prepare()
    lock,jars,libraries=base.verify_artifacts()
    oracle=lab.ROOT/"mods/apex/src/test/java/dev/apexlab/parity/VanillaFeatureCatalogOracle.java"
    helper=oracle.with_name("VanillaPlacementOracle.java")
    state_helper=oracle.with_name("VanillaBlockStateCodecOracle.java")
    sources=[oracle,helper,state_helper,Path(__file__),lab.ROOT/"tools/test_worldgen_parity.py",lab.ROOT/"tools/test_rust_parity.py",lab.ROOT/"tools/lab.py",lab.ROOT/"Cargo.toml",lab.ROOT/"Cargo.lock",lab.ROOT/"crates/apex-core/Cargo.toml",lab.ROOT/"crates/apex-world/Cargo.toml",
             *sorted((lab.ROOT/"crates/apex-core/src").rglob("*.rs")),*sorted((lab.ROOT/"crates/apex-world/src").rglob("*.rs")),lab.ROOT/"crates/apex-world/examples/probe/feature_catalog_fixture.rs"]
    tested_sources=base.source_hashes(sources)
    fixtures=list(corpus());inputs=build/"inputs.txt";inputs.write_text("".join(json.dumps(f,separators=(",",":"))+"\n" for f in fixtures),encoding="utf-8")
    resources=build/"catalog.json";resources.write_text(json.dumps(catalog(),separators=(",",":")),encoding="utf-8")
    fixture_paths=[inputs,resources];tested_fixtures=base.source_hashes(fixture_paths);classes=build/"classes";classes.mkdir(exist_ok=True)
    def run(command,name):
        with (build/(name+".log")).open("w",encoding="utf-8") as log:base.run(list(map(str,command)),stdout=log,stderr=subprocess.STDOUT)
    dependency_path=os.pathsep.join(map(str,libraries))
    run(["javac","--release",lock["minecraft"]["java_major"],"-proc:none","-cp",str(jars["server"])+os.pathsep+dependency_path,"-d",classes,oracle,helper,state_helper],"compile-java")
    for side,jar in jars.items():
        path=build/f"facts-{side}.json"
        run(["java","-Xmx512M","-cp",os.pathsep.join([str(classes),str(jar),dependency_path]),"dev.apexlab.parity.VanillaFeatureCatalogOracle","export",path],side+"-export")
        fixture_paths.append(path)
    if json.loads((build/"facts-client.json").read_text())!=json.loads((build/"facts-server.json").read_text()):raise ValueError("reference feature block states differ")
    tested_fixtures=base.source_hashes(fixture_paths)
    run(["cargo","build","--release","-p","apex-world","--example","world_probe"],"compile-rust")
    metadata=json.loads(subprocess.check_output(["cargo","metadata","--no-deps","--format-version","1"],cwd=lab.ROOT,text=True))
    binary=Path(metadata["target_directory"])/"release/examples"/("world_probe.exe" if os.name=="nt" else "world_probe")
    run([binary,"feature_catalog_fixture",build],"rust")
    references=[]
    for side,jar in jars.items():
        reference=build/f"{side}.txt"
        run(["java","-Xmx512M","-cp",os.pathsep.join([str(classes),str(jar),dependency_path]),"dev.apexlab.parity.VanillaFeatureCatalogOracle",side,build],side)
        matched=base.compare(reference,build/"rust.txt")
        references.append({"side":side,"jar_sha256":lab.digest(jar,"sha256"),"output_sha256":lab.digest(reference,"sha256"),"matched_output_lines":matched})
        print(f"{side}: {matched:,} feature-catalog output lines match Rust",flush=True)
    base.ensure_sources_unchanged(sources,tested_sources);base.ensure_sources_unchanged(fixture_paths,tested_fixtures)
    report={"schema":1,"minecraft":lock["minecraft"]["version"],"manifest_sha1":lock["minecraft"]["manifest_sha1"],"platform":platform.platform(),
            "java":subprocess.check_output(["java","--version"],text=True).splitlines()[0],"rustc":subprocess.check_output(["rustc","--version"],text=True).strip(),
            "fixtures":len(fixtures),"worldgen_random_modes":[False,True],"basic_features":3,"composition_features":7,"definitions":len(list(definitions())),"block_states":35723,"configured_block_features":3,"named_features":len(catalog()["features"]),"named_placed_features":len(catalog()["placed"]),"tag_files":len(catalog()["tags"]),"requested_placements":sum(f["repeats"] for f in fixtures),
            "sources_sha256":tested_sources,"fixtures_sha256":tested_fixtures,"rust_output_sha256":lab.digest(build/"rust.txt","sha256"),"references":references,
            "scope":"Actual Feature.CODEC and PlacedFeature.CODEC bind named and inline holders through RegistryOps and registered feature/placed-feature snapshots. Native TagLoader resolves ordered nested, duplicate, empty, optional-missing and required-missing placed-feature tags. Overlay accumulated success and non-short-circuit execution, including empty named tags, are compared. Root holders, named children, tag lists, mixed inline/named lists, namespace shorthand, unknown names and unselected malformed children are compared. Registry-bound fill-layer, single-block replacement and scattered-ore states execute through named roots, nested tags and composed placement. Registry-bound matching-block/fluid predicates also execute through filters, ordered volumes, environment scans and composed named features against the mutable world, including a flowing-water fill followed by repeated fluid-filtered replacement. Actual feature algorithms, nested placement, ordered world mutations, rejected writes, partial failures and direct and WorldgenRandom-wrapped legacy/xoroshiro streams execute through the same mutable world transport. Rust expands requested immutable resource roots with bounded dependency/node traversal; unused resources, cyclic references, registry reload/lifecycle, encoding, all feature algorithms and complete world generation remain outside this comparison."}


    lab.write_json(report_path,report);print(f"Scoped feature-catalog parity passed: {report_path}")


if __name__=="__main__":main()
