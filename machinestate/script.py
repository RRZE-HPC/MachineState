from .common import argparse, which, pexists, fopen, json, logging, os, sys, ENCODING, pjoin
from .common import DMIDECODE_FILE, DO_LIKWID, LIKWID_PATH, MODULECMD_PATH, VEOS_BASE, NVIDIA_PATH, CLINFO_PATH, DEFAULT_LOGLEVEL
from .common import MachineState
try:
    import yaml
except Exception:
    yaml = None

################################################################################
# Skript code
################################################################################

def load_structured_file(path: str):
    """Load JSON or YAML from a file. Prefer JSON; if that fails, try YAML."""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    # Try JSON first
    try:
        return json.loads(text)
    except Exception:
        pass
    # Try YAML
    if yaml is not None:
        try:
            return yaml.safe_load(text)
        except Exception:
            pass

    # If both failed, check if this looks like HTML and tailor the message
    t = text.lstrip().lower()
    if t.startswith("<!doctype html") or t.startswith("<html") or "<html" in t[:2000]:
        raise SystemExit(
            "[error] The provided file looks like HTML. Comparison expects a JSON or YAML state file."
        )

    # Generic failure
    if yaml is None:
        raise SystemExit(
            f"[error] Could not parse '{path}' as JSON, and PyYAML is not installed.\n"
            "Install with: pip install pyyaml"
        )
    raise SystemExit(f"[error] Could not parse '{path}' as JSON or YAML.")

def read_cli(cliargs):
    # Create CLI parser
    desc = 'Reads and outputs system information (JSON/HTML/YAML).'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-e', '--extended', action='store_true', default=False,
                        help='extended output (default: False)')
    parser.add_argument('-a', '--anonymous', action='store_true', default=False,
                        help='Remove host-specific information (default: False)')
    parser.add_argument('-c', '--config', default=False, action='store_true',
                        help='print configuration as JSON (files, commands, ...)')
    parser.add_argument('-s', '--sort', action='store_true', default=False,
                        help='sort structured output (default: False)')
    parser.add_argument('-i', '--indent', default=4, type=int,
                        help='indentation in structured output (default: 4)')
    parser.add_argument('-o', '--output', help='save to file (default: stdout)', default=None)
    parser.add_argument('-p', '--compare', help='compare current state to a saved state file (JSON or YAML)', default=None)
    parser.add_argument('-m', '--no-meta', action='store_false', default=True,
                        help='do not embed meta information in classes (recommended, default: True)')
    parser.add_argument('--json', help='generate JSON output (default if no other format is chosen)', action='store_true', default=False)
    parser.add_argument('--html', help='generate HTML page with CSS and JavaScript embedded instead of JSON', action='store_true', default=False)
    parser.add_argument('--yaml', help='generate YAML output instead of JSON', action='store_true', default=False)
    parser.add_argument('--configfile', help='Location of configuration file', default=None)
    parser.add_argument('--log', dest='loglevel', help='Loglevel (info, debug, warning, error)', default='info')
    parser.add_argument('executable', help='analyze executable (optional)', nargs='?', default=None)
    pargs = vars(parser.parse_args(cliargs))

    # Check if executable exists and is executable
    if pargs["executable"] is not None:
        abspath = which(pargs["executable"])
        if abspath is None or not pexists(abspath):
            raise ValueError("Executable '{}' does not exist".format(pargs["executable"]))
        if not os.access(abspath, os.X_OK):
            raise ValueError("Executable '{}' is not executable".format(pargs["executable"]))
    # Check if compare file exists and readable
    if pargs["compare"] is not None:
        if not pexists(pargs["compare"]):
            raise ValueError("State file '{}' does not exist".format(pargs["json"]))
        if not os.access(pargs["compare"], os.R_OK):
            raise ValueError("State file '{}' is not readable".format(pargs["json"]))
    # Check if configuration file exists and is readable
    if pargs["configfile"] is not None:
        if not pexists(pargs["configfile"]):
            raise ValueError("Configuration file '{}' does not exist".format(pargs["configfile"]))
        if not os.access(pargs["configfile"], os.R_OK):
            raise ValueError("Configuration file '{}' is not readable".format(pargs["configfile"]))
    if pargs["loglevel"]:
        numeric_level = getattr(logging, pargs["loglevel"].upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: {}'.format(pargs["loglevel"]))
        logging.basicConfig(level=numeric_level)
    return pargs

def read_config(config={"extended" : False, "anonymous" : False, "executable" : None}):

    if not ("extended" in config and "anonymous" in config and "executable" in config):
        raise ValueError("Given dict does not contain required keys: \
                          extended, anonymous and executable")
    configdict = {"dmifile" : DMIDECODE_FILE,
                  "likwid_enable" : DO_LIKWID,
                  "likwid_path" : LIKWID_PATH,
                  "modulecmd" : MODULECMD_PATH,
                  "vecmd_path" : VEOS_BASE,
                  "nvidia_path" : NVIDIA_PATH,
                  "loglevel" : DEFAULT_LOGLEVEL,
                  "clinfo_path" : CLINFO_PATH,
                  "anonymous" : False,
                  "extended" : False,
                 }
    searchfiles = []

    userfile = config.get("configfile", None)
    configdict["anonymous"] = config.get("anonymous", False)
    configdict["extended"] = config.get("extended", False)
    configdict["executable"] = config.get("executable", None)
    configdict["loglevel"] = config.get("loglevel", DEFAULT_LOGLEVEL)

    if userfile is not None:
        searchfiles.append(userfile)
    else:
        searchfiles = [pjoin(os.getcwd(), ".machinestate")]
        if "HOME" in os.environ:
            searchfiles.append(pjoin(os.environ["HOME"], ".machinestate"))
        searchfiles.append("/etc/machinestate.conf")
    for sfile in searchfiles:
        if pexists(sfile):
            sfp = fopen(sfile)
            if sfp:
                sstr = sfp.read().decode(ENCODING)
                if len(sstr) > 0:
                    try:
                        tmpdict = json.loads(sstr)
                        configdict.update(tmpdict)
                    except:
                        exce = "Configuration file '{}' not valid JSON".format(userfile)
                        raise ValueError(exce)
                sfp.close()
                break

    if configdict["loglevel"]:
        numeric_level = getattr(logging, configdict["loglevel"].upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: {}'.format(configdict["loglevel"]))
        logging.basicConfig(level=numeric_level)

    return configdict


base_js = """
<script>
var acc = document.getElementsByClassName("accordion");
var i;

for (i = 0; i < acc.length; i++) {
  acc[i].addEventListener("click", function() {
    this.classList.toggle("active");
    var children = this.parentNode.childNodes;
    children.forEach(child => {
        if(child.style) {
    		if (child.style.maxHeight) {
        		child.style.maxHeight = null;
       		} else {
	        	child.style.maxHeight = child.scrollHeight + "px";
    	    }
        }
    });
    adjust(this.parentNode);
  });
}

var bExpand = document.getElementsByClassName("option expandable")[0];
var bCollaps = document.getElementsByClassName("option collapsible")[0];

bExpand.addEventListener("click", function() {
	var accNonActive = Array.prototype.filter.call(acc, function(elem, i, acc) {
		return !elem.className.includes("active");
	});
	for (i = 0; i < accNonActive.length; i++) {
		accNonActive[i].click();
	}
});

bCollaps.addEventListener("click", function() {
	var accActive = Array.prototype.filter.call(acc, function(elem, i, acc) {
		return elem.className.includes("active");
	});
	for (i = accActive.length - 1; i >= 0; i--) {
		accActive[i].click();
	}
});

function adjust(node) {
	if(node.style) {
        node.style.maxHeight = 10 * window.innerHeight + "px";
    }
    if(node.parentNode){
    	adjust(node.parentNode);
	}
}
</script>
"""
base_css = """
<style>
.accordion {
  background-color: #eee;
  color: #444;
  cursor: pointer;
  padding: 18px;
  width: 98vw;
  border: none;
  text-align: left;
  outline: none;
  font-size: 15px;
  transition: 0.4s;
}

.active, .accordion:hover {
  background-color: #ccc;
}

.accordion:after {
  content: '\\002B';
  color: #777;
  font-weight: bold;
  float: right;
  margin-left: 5px;
}

.active:after {
  content: "\\2212";
}

.panel {
  padding: 0 18px;
  background-color: white;
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.2s ease-out;
  width: 97vw;
}

.option {
  float: left;
  background-color: #555555;
  border: none;
  color: white;
  padding: 15px 32px;
  text-align: center;
  text-decoration: none;
  display: inline-block;
  font-size: 15px;
}

.expandable {
  background-color: #4CAF50;
  width: 49vw;
}

.collapsible {
  background-color: #f44336;
  width: 49vw;
}
</style>
"""

base_html = """
<!DOCTYPE html>
<html lang="en">
<head>
<title>MachineState</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta charset="UTF-8">
{css}
</head>

<body>
<button class="option expandable">Expand all</button>
<button class="option collapsible">Collapse all</button>
{table}
{script}
</body>
</html>
"""

def get_html(cls, css=True, js=True):
    add_css = base_css if css is True else ""
    add_js = base_js if js is True else ""
    table = cls.get_html()
    return base_html.format(table=table, css=add_css, script=add_js)


def main():
    try:
        # Read command line arguments
        cliargs = read_cli(sys.argv[1:])
        # Read configuration from configuration file
        runargs = read_config(cliargs)
    except Exception as e:
        import traceback
        print("[fatal] initialization failed:", e)
        traceback.print_exc()
        sys.exit(1)

    # Initialize MachineState class
    mstate = MachineState(**runargs)
    
    # Generate subclasses and update (wrap to show the failing path)
    try:
        mstate.generate()
        mstate.update()
    except OSError as e:
        import traceback
        print("[probe] OSError while probing:", e)
        traceback.print_exc()
        sys.exit(1)
    # Generate subclasses of MachineState
    mstate.generate()
    # Update the current state
    mstate.update()

    # Compare current state to a saved file
    if cliargs["compare"] is not None:
        curr_json = mstate.get_json(
            sort=cliargs["sort"],
            intend=cliargs["indent"],
            meta=cliargs["no_meta"]
        )
        curr_obj = json.loads(curr_json)
        ref_obj = load_structured_file(cliargs["compare"])

        if curr_obj == ref_obj:
            print("Current state is identical to '{}'".format(cliargs["compare"]))
        else:
            print("Current state differs from '{}'".format(cliargs["compare"]))
        sys.exit(0)
    if not cliargs["config"]:
        json_str = mstate.get_json(
            sort=cliargs["sort"],
            intend=cliargs["indent"],
            meta=cliargs["no_meta"]
        )
    else:
        json_str = mstate.get_config(
            sort=cliargs["sort"],
            intend=cliargs["indent"]
        )
    dict_obj = json.loads(json_str)

    # serialize according to requested format
    def write_json(fp):
        # Use standard json to ensure indent and sort flags are applied (again) consistently
        json.dump(dict_obj, fp, ensure_ascii=False, indent=cliargs["indent"], sort_keys=cliargs["sort"])
        fp.write("\n")

    def write_yaml(fp):
        if yaml is None:
            raise SystemExit(
                "[error] YAML output requested but PyYAML is not installed.\n"
                "Install with: pip install pyyaml"
            )
        fp.write(
            yaml.safe_dump(
                dict_obj,
                allow_unicode=True,
                sort_keys=cliargs["sort"],
                default_flow_style=False,
                indent=cliargs["indent"],
            )
        )

    def write_html(fp):
        # Your HTML uses the live object methods; sorting/meta were already applied when building dict_obj
        fp.write(get_html(mstate))
        fp.write("\n")

   # Stdout vs file
    def want_json(args):
        return args.get("json", False) or not (args.get("html") or args.get("yaml"))

    if not cliargs["output"]:
        if cliargs["html"]:
            write_html(sys.stdout)
        elif cliargs.get("yaml", False):
            write_yaml(sys.stdout)
        elif want_json(cliargs):
            write_json(sys.stdout)
    else:
        with open(cliargs["output"], "w", encoding="utf-8") as outfp:
            if cliargs["html"]:
                write_html(outfp)
            elif cliargs.get("yaml", False):
                write_yaml(outfp)
            elif want_json(cliargs):
                write_json(outfp)

    sys.exit(0)  
#    # This part is for testing purposes
#    n = OperatingSystemInfo(extended=cliargs["extended"])
#    n.generate()
#    n.update()
#    ndict = n.get()
#    copydict = deepcopy(ndict)
#    print(n == copydict)
#    print(n.get_json(sort=cliargs["sort"], intend=cliargs["indent"]))

__main__ = main
if __name__ == "__main__":
    main()