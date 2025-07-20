
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import BaseGraph


def visualize_base_graph(graph: "BaseGraph", filename: str) -> None:
    """Generate a visualization of the graph with clean, readable flow."""
    if not graph._action_nodes or not graph._start_action_name:
        raise ValueError("No actions defined in graph")
    
    # Build our own mermaid code for better control over layout
    mermaid_lines = ["graph TD"]  # Top-Down layout
    
    # Track which nodes we've already added
    added_nodes = set()
    
    # Style definitions
    mermaid_lines.append("    %% Styles")
    mermaid_lines.append("    classDef startNode fill:#4CAF50,stroke:#333,stroke-width:2px,color:#fff")
    mermaid_lines.append("    classDef endNode fill:#f44336,stroke:#333,stroke-width:2px,color:#fff")
    mermaid_lines.append("    classDef defaultNode fill:#2196F3,stroke:#333,stroke-width:2px,color:#fff")
    mermaid_lines.append("")
    
    # Helper to get clean node ID
    def get_node_id(action_name: str) -> str:
        return action_name.replace(" ", "_").replace("-", "_")
    
    # Helper to add a node if not already added
    def add_node(action_name: str, is_start: bool = False, is_end: bool = False) -> None:
        if action_name not in added_nodes:
            node_id = get_node_id(action_name)
            # Use the action name as the display label
            display_name = action_name
            
            if is_start:
                mermaid_lines.append(f"    {node_id}[{display_name}]:::startNode")
            elif is_end:
                mermaid_lines.append(f"    {node_id}[{display_name}]:::endNode")
            else:
                mermaid_lines.append(f"    {node_id}[{display_name}]:::defaultNode")
            added_nodes.add(action_name)
    
    # Add all nodes and connections
    mermaid_lines.append("    %% Nodes and connections")
    
    # Start with the start node
    add_node(graph._start_action_name, is_start=True)
    
    # Process all actions to find connections
    for action_name in graph._action_nodes:
        action_func = getattr(graph, action_name, None)
        if action_func and hasattr(action_func, '_action_settings'):
            settings = action_func._action_settings
            
            # Add the node
            add_node(action_name, is_end=settings.terminates)
            
            # Add connections based on 'next' settings
            if settings.next:
                source_id = get_node_id(action_name)
                
                if isinstance(settings.next, str):
                    # Simple string case
                    target_id = get_node_id(settings.next)
                    add_node(settings.next)
                    mermaid_lines.append(f"    {source_id} --> {target_id}")
                    
                elif isinstance(settings.next, list):
                    # List case - branches to multiple nodes
                    for next_action in settings.next:
                        if isinstance(next_action, str):
                            target_id = get_node_id(next_action)
                            add_node(next_action)
                            mermaid_lines.append(f"    {source_id} --> {target_id}")
                            
                elif hasattr(settings.next, '__class__') and settings.next.__class__.__name__ == 'SelectionStrategy':
                    # SelectionStrategy case
                    if settings.next.actions:
                        # Show all possible paths with a decision diamond
                        decision_id = f"{source_id}_decision"
                        mermaid_lines.append(f"    {source_id} --> {decision_id}{{LLM Selection}}")
                        
                        for next_action in settings.next.actions:
                            target_id = get_node_id(next_action)
                            add_node(next_action)
                            mermaid_lines.append(f"    {decision_id} --> {target_id}")
                    else:
                        # If no specific actions, it can go to any node
                        # For visualization, show connections to all non-start nodes
                        decision_id = f"{source_id}_decision"
                        mermaid_lines.append(f"    {source_id} --> {decision_id}{{LLM Selection}}")
                        
                        for other_action in graph._action_nodes:
                            if other_action != action_name and other_action != graph._start_action_name:
                                target_id = get_node_id(other_action)
                                add_node(other_action)
                                mermaid_lines.append(f"    {decision_id} -.-> {target_id}")
    
    # If start node has no explicit next, but there are other nodes, show possible connections
    start_func = getattr(graph, graph._start_action_name, None)
    if start_func and hasattr(start_func, '_action_settings'):
        if not start_func._action_settings.next and len(graph._action_nodes) > 1:
            source_id = get_node_id(graph._start_action_name)
            # Find end nodes (terminates=True) to connect to
            for action_name in graph._action_nodes:
                if action_name != graph._start_action_name:
                    action_func = getattr(graph, action_name, None)
                    if action_func and hasattr(action_func, '_action_settings'):
                        if action_func._action_settings.terminates:
                            target_id = get_node_id(action_name)
                            add_node(action_name, is_end=True)
                            mermaid_lines.append(f"    {source_id} --> {target_id}")
    
    # Join all lines
    mermaid_code = "\n".join(mermaid_lines)
    
    # Render the mermaid diagram and save it
    try:
        import subprocess
        import tempfile
        import os
        import shutil
        
        # Check if mmdc (mermaid CLI) is available
        if shutil.which('mmdc') is None:
            raise FileNotFoundError("mermaid-cli (mmdc) not found. Install with: npm install -g @mermaid-js/mermaid-cli")
        
        # Create a temporary mermaid file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as temp_file:
            temp_file.write(mermaid_code)
            temp_mmd_path = temp_file.name
        
        try:
            # Determine output format from filename extension
            output_format = 'png'  # default
            if filename.lower().endswith('.svg'):
                output_format = 'svg'
            elif filename.lower().endswith('.pdf'):
                output_format = 'pdf'
            
            # Use mermaid CLI to render the diagram
            cmd = ['mmdc', '-i', temp_mmd_path, '-o', filename]
            
            # Add format flag only if not PNG (PNG is default)
            if output_format != 'png':
                cmd.extend(['-f', output_format])
            
            # Add theme and background color
            cmd.extend(['-t', 'default', '-b', 'transparent'])
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            if result.returncode == 0:
                print(f"Graph visualization saved to: {filename}")
            else:
                raise subprocess.CalledProcessError(result.returncode, result.args, result.stderr)
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_mmd_path):
                os.unlink(temp_mmd_path)
                
    except FileNotFoundError as e:
        # Provide helpful error message for missing mermaid CLI
        print(f"Warning: {e}")
        # Save as .mmd file instead
        mmd_filename = filename.rsplit('.', 1)[0] + '.mmd'
        with open(mmd_filename, "w") as f:
            f.write(mermaid_code)
        print(f"Mermaid code saved to: {mmd_filename}")
        print("To render as PNG, install mermaid-cli: npm install -g @mermaid-js/mermaid-cli")
        
    except subprocess.CalledProcessError as e:
        # Handle mermaid CLI errors
        print(f"Error rendering mermaid diagram: {e.stderr if e.stderr else str(e)}")
        # Save as .mmd file as fallback
        mmd_filename = filename.rsplit('.', 1)[0] + '.mmd'
        with open(mmd_filename, "w") as f:
            f.write(mermaid_code)
        print(f"Mermaid code saved to: {mmd_filename} (rendering failed)")
        
    except Exception as e:
        # General fallback: save the mermaid code
        print(f"Unexpected error: {e}")
        mmd_filename = filename.rsplit('.', 1)[0] + '.mmd'
        with open(mmd_filename, "w") as f:
            f.write(mermaid_code)
        print(f"Mermaid code saved to: {mmd_filename}")