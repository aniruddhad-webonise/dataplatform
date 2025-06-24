#!/usr/bin/env python3
"""
Manual Resource Cleanup Script for the MCP SQL Analytics Server.
Reuses existing ResourceManager logic for cleaning up resources.
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from core.resource_manager import ResourceManager

async def cleanup_resources(cleanup_type: str, resource_type: str = None, 
                          resource_uri: str = None, force: bool = False):
    """Clean up resources based on specified criteria."""
    
    resource_manager = ResourceManager()
    
    print(f"🧹 Resource Cleanup - Type: {cleanup_type}")
    print("=" * 50)
    
    if cleanup_type == "all":
        if not force:
            confirm = input("⚠️  This will delete ALL resources. Are you sure? (y/N): ")
            if confirm.lower() != 'y':
                print("❌ Cleanup cancelled.")
                return
        
        # Get all resources
        all_resources = list(resource_manager.resources.keys())
        print(f"🗑️  Deleting {len(all_resources)} resources...")
        
        for uri in all_resources:
            resource_manager._delete_resource(uri)
            print(f"   ✅ Deleted: {uri}")
        
        print(f"🎉 Successfully cleaned {len(all_resources)} resources.")
    
    elif cleanup_type == "expired":
        print("🕐 Cleaning expired resources...")
        
        # Get current resources count
        initial_count = len(resource_manager.resources)
        
        # Run cleanup (this will delete expired resources)
        resource_manager._cleanup_expired_resources()
        
        # Get final count
        final_count = len(resource_manager.resources)
        deleted_count = initial_count - final_count
        
        print(f"🎉 Cleaned {deleted_count} expired resources.")
        print(f"📊 Remaining resources: {final_count}")
    
    elif cleanup_type == "by_type":
        if not resource_type:
            print("❌ Error: resource_type is required for 'by_type' cleanup.")
            return
        
        if not force:
            confirm = input(f"⚠️  This will delete all '{resource_type}' resources. Are you sure? (y/N): ")
            if confirm.lower() != 'y':
                print("❌ Cleanup cancelled.")
                return
        
        # Find resources of specified type
        resources_to_delete = []
        for uri, metadata in resource_manager.resources.items():
            if metadata.get("type") == resource_type:
                resources_to_delete.append(uri)
        
        print(f"🗑️  Deleting {len(resources_to_delete)} '{resource_type}' resources...")
        
        for uri in resources_to_delete:
            resource_manager._delete_resource(uri)
            print(f"   ✅ Deleted: {uri}")
        
        print(f"🎉 Successfully cleaned {len(resources_to_delete)} '{resource_type}' resources.")
    
    elif cleanup_type == "specific":
        if not resource_uri:
            print("❌ Error: resource_uri is required for 'specific' cleanup.")
            return
        
        if resource_uri not in resource_manager.resources:
            print(f"❌ Error: Resource '{resource_uri}' not found.")
            return
        
        if not force:
            confirm = input(f"⚠️  This will delete resource '{resource_uri}'. Are you sure? (y/N): ")
            if confirm.lower() != 'y':
                print("❌ Cleanup cancelled.")
                return
        
        print(f"🗑️  Deleting specific resource: {resource_uri}")
        resource_manager._delete_resource(resource_uri)
        print(f"🎉 Successfully deleted: {resource_uri}")
    
    else:
        print(f"❌ Error: Unknown cleanup type '{cleanup_type}'.")
        return
    
    # Show remaining resources
    remaining_resources = await resource_manager.list_resources()
    print(f"\n📊 Remaining resources: {len(remaining_resources)}")
    for resource in remaining_resources:
        print(f"   - {resource.uri} ({resource.name})")

def main():
    """Main entry point for the cleanup script."""
    parser = argparse.ArgumentParser(
        description="Manual Resource Cleanup for MCP SQL Analytics Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cleanup_resources.py --type all --force
  python cleanup_resources.py --type expired
  python cleanup_resources.py --type by_type --resource-type table --force
  python cleanup_resources.py --type specific --resource-uri resource://tables/abc123
        """
    )
    
    parser.add_argument(
        "--type", "-t",
        required=True,
        choices=["all", "expired", "by_type", "specific"],
        help="Type of cleanup to perform"
    )
    
    parser.add_argument(
        "--resource-type", "-rt",
        choices=["table", "schema", "chart", "ml"],
        help="Resource type for 'by_type' cleanup"
    )
    
    parser.add_argument(
        "--resource-uri", "-ru",
        help="Specific resource URI for 'specific' cleanup"
    )
    
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Skip confirmation prompts"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.type == "by_type" and not args.resource_type:
        print("❌ Error: --resource-type is required for 'by_type' cleanup.")
        sys.exit(1)
    
    if args.type == "specific" and not args.resource_uri:
        print("❌ Error: --resource-uri is required for 'specific' cleanup.")
        sys.exit(1)
    
    # Run cleanup
    try:
        asyncio.run(cleanup_resources(
            cleanup_type=args.type,
            resource_type=args.resource_type,
            resource_uri=args.resource_uri,
            force=args.force
        ))
    except KeyboardInterrupt:
        print("\n❌ Cleanup interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 