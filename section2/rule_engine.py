# ==============================================================
#   Algo2Code Compiler - Section 2
#   File: rule_engine.py
# ==============================================================

import re
import os


class RuleEngine:
    def __init__(self, rule_file_path: str):
        self.rules: dict        = {}
        self.config: dict       = {}
        self.header_lines: list = []
        self.footer_lines: list = []
        self.file_type: str     = self._detect_file_type(rule_file_path)
        self._load(rule_file_path)

    def _detect_file_type(self, path: str) -> str:
        """Detect if file is lex (.l) or yacc (.y) based on extension"""
        _, ext = os.path.splitext(path)
        return 'lex' if ext.lower() == '.l' else 'yacc' if ext.lower() == '.y' else 'unknown'

    def get_file_type(self) -> str:
        return self.file_type

    def get_rule(self, node_type: str):
        return self.rules.get(node_type)

    def get_config(self, key: str, default=None):
        return self.config.get(key, default)

    def get_header(self) -> list:
        return self.header_lines

    def get_footer(self) -> list:
        return self.footer_lines

    def _load(self, path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Rule file not found: {path}")
        with open(path, 'r', encoding='utf-8') as fh:
            raw = fh.read()

        if self.file_type == 'lex':
            self._load_lex(raw)
        elif self.file_type == 'yacc':
            self._load_yacc(raw)
        else:
            raise ValueError(f"Unsupported file type: {self.file_type}")

    def _load_lex(self, raw: str):
        """Load lex-style rule file (.l extension)"""
        # Strip /* ... */ comments
        raw = re.sub(r'/\*.*?\*/', '', raw, flags=re.DOTALL)

        # Prologue %{ ... %}
        prologue = re.search(r'%\{(.*?)%\}', raw, re.DOTALL)
        if prologue:
            self._parse_prologue(prologue.group(1))

        # Rules section between %% markers
        parts      = re.split(r'^%%\s*$', raw, flags=re.MULTILINE)
        rules_text = parts[1] if len(parts) >= 2 else ''
        self._parse_rules(rules_text)

    def _load_yacc(self, raw: str):
        """Load yacc-style rule file (.y extension)"""
        # Strip /* ... */ comments
        raw = re.sub(r'/\*.*?\*/', '', raw, flags=re.DOTALL)

        # Parse %{ ... %} section for configuration
        prologue = re.search(r'%\{(.*?)%\}', raw, re.DOTALL)
        if prologue:
            self._parse_yacc_prologue(prologue.group(1))

        # Parse %% ... %% section for grammar rules
        parts = re.split(r'^%%\s*$', raw, flags=re.MULTILINE)
        if len(parts) >= 2:
            grammar_text = parts[1]
            # Remove any trailing %% section
            grammar_parts = grammar_text.split('%%', 1)
            grammar_text = grammar_parts[0]
            self._parse_yacc_rules(grammar_text)

    def _parse_yacc_prologue(self, text: str):
        """Parse yacc prologue section for configuration"""
        for raw_line in text.splitlines():
            # Look for #define statements
            m = re.match(r'^\s*#define\s+(\w+)\s+(.*?)\s*$', raw_line)
            if m:
                key = m.group(1)
                val = m.group(2).strip('"')
                if key == 'HEADER':
                    self.header_lines.append(val)
                elif key == 'FOOTER':
                    self.footer_lines.append(val)
                else:
                    self.config[key] = val
                continue
            
            # Look for array initializations
            m = re.match(r'^\s*static\s+char\*\s+(\w+)\[\s*\]\s*=\s*\{(.*?)\};', raw_line, re.DOTALL)
            if m:
                array_name = m.group(1)
                if array_name == 'header_code':
                    self._parse_array_init(m.group(2), self.header_lines)
                elif array_name == 'footer_code':
                    self._parse_array_init(m.group(2), self.footer_lines)

    def _parse_array_init(self, init_text: str, target_list: list):
        """Parse C array initialization like {"str1", "str2"}"""
        # Extract quoted strings
        strings = re.findall(r'"([^"]*)"', init_text)
        target_list.extend(strings)

    def _parse_yacc_rules(self, text: str):
        """Parse yacc grammar rules"""
        # Split into individual rule blocks
        rule_blocks = re.split(r'^([A-Za-z_]\w*)\s*:', text, flags=re.MULTILINE)
        
        # Skip the first element (before first rule name)
        for i in range(1, len(rule_blocks), 2):
            if i + 1 >= len(rule_blocks):
                break
                
            rule_name = rule_blocks[i].strip()
            rule_content = rule_blocks[i + 1]
            
            # Handle statement rule specially since it contains our AST rules
            if rule_name == 'statement':
                self._parse_statement_rule(rule_content)
                continue
            
            # Skip other grammar production rules
            if rule_name in ['program', 'statements', 'expression', 'condition']:
                continue
            
            # Parse other rules (if any)
            self._parse_generic_rule(rule_name, rule_content)

    def _parse_statement_rule(self, rule_content: str):
        """Parse the statement rule which contains our AST node rules"""
        # Parse alternatives separated by |
        alternatives = re.split(r'\s*\|\s*', rule_content)
        
        for alt in alternatives:
            alt = alt.strip()
            if not alt:
                continue
                
            # Remove trailing semicolon
            alt = alt.rstrip(';')
            
            # Extract the pattern and action - look for the first { that starts the action block
            pattern_match = re.match(r'^([^{}\n]*\([^{}\n]*\)[^{}\n]*)\s*\{([^{}]*)\}', alt, re.DOTALL)
            if pattern_match:
                pattern = pattern_match.group(1).strip()
                action = pattern_match.group(2).strip()
                
                # Normalize whitespace in pattern for matching
                normalized_pattern = re.sub(r'\s+', ' ', pattern)
                
                # Extract token name and parameters from pattern
                # Pattern should be like: READ '(' IDENTIFIER ')'
                # Note: the parentheses might be quoted in the pattern
                token_match = re.match(r'([A-Z_]\w*)\s*[\'"]?\([\'"]?\s*([^)]*)\s*[\'"]?\)[\'"]?', normalized_pattern)
                if token_match:
                    token_name = token_match.group(1)
                    params_str = token_match.group(2)
                    # Clean up parameters - remove quotes and split by comma
                    params = []
                    if params_str:
                        for p in params_str.split(','):
                            p = p.strip()
                            # Remove surrounding quotes if present
                            if p.startswith("'") and p.endswith("'"):
                                p = p[1:-1]
                            elif p.startswith('"') and p.endswith('"'):
                                p = p[1:-1]
                            # Remove trailing quotes
                            elif p.endswith("'") or p.endswith('"'):
                                p = p[:-1]
                            # Remove leading quotes  
                            elif p.startswith("'") or p.startswith('"'):
                                p = p[1:]
                            # Final strip to remove any remaining whitespace
                            p = p.strip()
                            if p:
                                params.append(p)
                    
                    # Parse action to extract template
                    template = self._extract_yacc_template(action)
                    
                    if template:
                        rule = {
                            'kind': 'SIMPLE',
                            'params': params,
                            'open_lines': [template],
                            'else_lines': [],
                            'close_lines': []
                        }
                        
                        self.rules[token_name] = rule

    def _parse_generic_rule(self, rule_name: str, rule_content: str):
        """Parse a generic yacc rule"""
        # Parse alternatives separated by |
        alternatives = re.split(r'\s*\|\s*', rule_content)
        
        for alt in alternatives:
            alt = alt.strip()
            if not alt or alt.endswith(';'):
                continue
                
            # Remove trailing semicolon
            alt = alt.rstrip(';')
            
            # Extract the pattern and action
            parts = re.split(r'\s*\{\s*([^{}]*)\s*\}\s*', alt, maxsplit=1)
            if len(parts) >= 2:
                pattern = parts[0].strip()
                action = parts[1].strip()
                
                # Extract parameters from pattern
                param_match = re.search(r'\(\s*([^)]*)\s*\)', pattern)
                params = []
                if param_match:
                    params_str = param_match.group(1)
                    params = [p.strip() for p in params_str.split(',') if p.strip()]
                
                # Parse action to extract template
                template = self._extract_yacc_template(action)
                
                if template:
                    rule = {
                        'kind': 'SIMPLE',
                        'params': params,
                        'open_lines': [template],
                        'else_lines': [],
                        'close_lines': []
                    }
                    
                    # Create a more descriptive rule name
                    if params:
                        param_desc = '_'.join(params[:2])  # Use first 2 params
                        full_rule_name = f"{rule_name}_{param_desc}"
                    else:
                        full_rule_name = rule_name
                        
                    self.rules[full_rule_name] = rule

    def _extract_yacc_template(self, action: str) -> str:
        """Extract template from yacc action code"""
        # Look for sprintf patterns like sprintf(code, "template", ...)
        m = re.search(r'sprintf\s*\(\s*[^,]*,\s*"([^"]*)"', action)
        if m:
            return m.group(1)
        
        # Look for simple string assignments
        m = re.search(r'[^=]*=\s*"([^"]*)"', action)
        if m:
            return m.group(1)
        
        # Look for printf patterns
        m = re.search(r'printf\s*\(\s*"([^"]*)"', action)
        if m:
            return m.group(1)
        
        return ""

    def _parse_prologue(self, text: str):
        """
        Parse KEY = value pairs.  Regex captures value verbatim
        (no strip) so HEADER lines with special chars are preserved.
        """
        for raw_line in text.splitlines():
            m = re.match(r'^\s*([A-Z_]+)\s*=\s*(.*?)\s*$', raw_line)
            if not m:
                continue
            key = m.group(1)
            val = m.group(2)
            if key == 'HEADER':
                self.header_lines.append(val)
            elif key == 'FOOTER':
                self.footer_lines.append(val)
            else:
                self.config[key] = val

    def _parse_rules(self, text: str):
        """
        Rule format:
            NodeType(param1, param2)
                [BLOCK | BLOCK_ELSE]
                -> template line
                [ELSE]
                -> template line
                [CLOSE]
                -> template line
            ;
        """
        pattern = re.compile(
            r'^([A-Za-z_]\w*)\(([^)]*)\)\s*\n(.*?)^;',
            re.MULTILINE | re.DOTALL
        )
        for m in pattern.finditer(text):
            node_type = m.group(1).strip()
            params    = [p.strip() for p in m.group(2).split(',') if p.strip()]
            rule      = self._parse_body(m.group(3))
            rule['params'] = params
            self.rules[node_type] = rule

    def _parse_body(self, body: str) -> dict:
        rule    = {'kind': 'SIMPLE', 'open_lines': [], 'else_lines': [], 'close_lines': []}
        section = 'open'
        for raw_line in body.splitlines():
            tok = raw_line.strip()
            if not tok:
                continue
            if tok == 'BLOCK':      rule['kind'] = 'BLOCK';      continue
            if tok == 'BLOCK_ELSE': rule['kind'] = 'BLOCK_ELSE'; continue
            if tok == 'ELSE':       section = 'else';             continue
            if tok == 'CLOSE':      section = 'close';            continue
            m = re.match(r'^->\s?(.*)|^→\s?(.*)', tok)
            if m:
                tmpl = m.group(1) if m.group(1) is not None else m.group(2)
                rule[f'{section}_lines'].append(tmpl)
        return rule

    def dump(self):
        print(f"  Config : {self.config}")
        print(f"  Header : {self.header_lines}")
        print(f"  Footer : {self.footer_lines}")
        for name, rule in self.rules.items():
            print(f"\n  [{name}] kind={rule['kind']} params={rule['params']}")
            print(f"    open  : {rule['open_lines']}")
            if rule['else_lines']:  print(f"    else  : {rule['else_lines']}")
            if rule['close_lines']: print(f"    close : {rule['close_lines']}")
