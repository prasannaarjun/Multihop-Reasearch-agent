"""
Test runner for the Multi-hop Research Agent system.
"""

import unittest
import sys
import os
import argparse
from io import StringIO

# Add the parent directory to the path so we can import the agents
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_tests():
    """Run all tests."""
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()

def run_specific_test(test_module):
    """Run a specific test module."""
    try:
        # Import the test module
        module = __import__(test_module)
        
        # Create test suite
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(module)
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result.wasSuccessful()
    except ImportError as e:
        print(f"Error importing {test_module}: {e}")
        return False

def run_tests_by_category(category):
    """Run tests by category."""
    categories = {
        'shared': ['test_shared_models', 'test_shared_exceptions', 'test_shared_interfaces'],
        'research': ['test_research_agent'],
        'chat': ['test_chat_agent'],
        'integration': ['test_integration'],
        'auth': ['test_auth'],
        'utils': ['test_utils']
    }
    
    if category not in categories:
        print(f"Unknown category: {category}")
        print(f"Available categories: {', '.join(categories.keys())}")
        return False
    
    success = True
    for test_module in categories[category]:
        print(f"\nRunning {test_module}...")
        if not run_specific_test(test_module):
            success = False
    
    return success

def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description='Run Multi-hop Research Agent tests')
    parser.add_argument('--module', '-m', help='Run specific test module')
    parser.add_argument('--category', '-c', help='Run tests by category (shared, research, chat, integration, auth, utils)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--list', '-l', action='store_true', help='List available test modules')
    
    args = parser.parse_args()
    
    if args.list:
        print("Available test modules:")
        test_files = [f for f in os.listdir(os.path.dirname(__file__)) if f.startswith('test_') and f.endswith('.py')]
        for test_file in sorted(test_files):
            module_name = test_file[:-3]  # Remove .py extension
            print(f"  - {module_name}")
        return
    
    if args.module:
        # Run specific module
        success = run_specific_test(args.module)
    elif args.category:
        # Run tests by category
        success = run_tests_by_category(args.category)
    else:
        # Run all tests
        success = run_tests()
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()

