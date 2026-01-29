"""
Example usage of the Bot Conductor Module

This script demonstrates how to use the Bot Conductor to extract data
from Phoenix using multiple concurrent bots.
"""

from bot_conductor import BotConductor
import logging

# Configure logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main example function."""
    
    print("=" * 80)
    print("Bot Conductor Module - Example Usage")
    print("=" * 80)
    
    # 1. Initialize the Bot Conductor
    print("\n1. Initializing Bot Conductor...")
    conductor = BotConductor(
        max_workers=5,      # Use up to 5 concurrent bots
        batch_size=30       # Each bot handles up to 30 PRIs
    )
    print("   ✓ Conductor initialized with 5 workers and batch size of 30")
    
    # 2. Prepare PRI list
    print("\n2. Preparing PRI list...")
    pri_list = [f"PRI{i:04d}" for i in range(1, 76)]  # 75 PRIs
    print(f"   ✓ Created list of {len(pri_list)} PRIs")
    
    # 3. Divide PRIs into batches
    print("\n3. Dividing PRIs into batches...")
    batches = conductor.divide_pris(pri_list)
    print(f"   ✓ Divided into {len(batches)} batches:")
    for i, batch in enumerate(batches):
        print(f"      - Batch {i + 1}: {len(batch)} PRIs")
    
    # 4. Configure Phoenix credentials
    print("\n4. Configuring Phoenix credentials...")
    phoenix_credentials = {
        'base_url': 'https://phoenix.example.com',
        'username': 'demo_user',
        'password': 'demo_password'
    }
    print("   ✓ Credentials configured")
    
    # 5. Extract data
    print("\n5. Starting data extraction...")
    print("   (This will use mock data since we're not connected to a real Phoenix server)")
    
    try:
        results = conductor.extract_data(
            pri_list=pri_list,
            phoenix_credentials=phoenix_credentials
        )
        
        print(f"\n   ✓ Extraction completed:")
        print(f"      - Total PRIs: {results['total_pris']}")
        print(f"      - Successful: {results['successful']}")
        print(f"      - Failed: {results['failed_count']}")
        
    except Exception as e:
        print(f"\n   ✗ Extraction failed: {str(e)}")
        results = None
    
    # 6. Generate statistics
    if results:
        print("\n6. Generating statistics...")
        stats = conductor.get_statistics(results)
        print(f"   ✓ Statistics:")
        print(f"      - Success Rate: {stats['success_rate']:.2f}%")
        print(f"      - Total Processed: {stats['total_pris_processed']}")
    
    # 7. Validate results with sample PRIs
    if results and results['successful'] > 0:
        print("\n7. Validating results...")
        sample_pris = pri_list[:5]  # Use first 5 PRIs as samples
        
        validation_report = conductor.validate_results(
            results=results,
            sample_pris=sample_pris
        )
        
        print(f"   ✓ Validation report:")
        print(f"      - Overall Valid: {validation_report['overall_valid']}")
        print(f"      - Valid Count: {validation_report['valid_count']}/{validation_report['total_count']}")
        
        if validation_report.get('sample_validation'):
            sv = validation_report['sample_validation']
            print(f"      - Sample Validation: {sv['found_samples']}/{sv['total_samples']} found")
    
    print("\n" + "=" * 80)
    print("Example completed!")
    print("=" * 80)


if __name__ == '__main__':
    main()
