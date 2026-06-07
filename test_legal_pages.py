"""
Test script to verify Terms and Privacy pages work correctly
"""
from integrated_app import app
import sys

def test_routes():
    """Test that all routes return successfully"""
    print("🧪 Testing Flask Routes...\n")

    with app.test_client() as client:
        routes_to_test = [
            ('/', 'Home Page'),
            ('/terms', 'Terms of Service'),
            ('/privacy', 'Privacy Policy')
        ]

        all_passed = True

        for route, name in routes_to_test:
            try:
                response = client.get(route)
                status = response.status_code

                if status == 200:
                    content_length = len(response.data)
                    print(f"✅ {name:25} - Status: {status} - Size: {content_length:,} bytes")
                else:
                    print(f"❌ {name:25} - Status: {status} - FAILED")
                    all_passed = False

            except Exception as e:
                print(f"❌ {name:25} - Error: {str(e)}")
                all_passed = False

        print("\n" + "="*60)
        if all_passed:
            print("🎉 All routes working correctly!")
        else:
            print("⚠️  Some routes failed. Check errors above.")
        print("="*60)

        return all_passed

def verify_templates():
    """Verify all template files exist"""
    print("\n📁 Verifying Template Files...\n")

    from pathlib import Path

    templates_dir = Path(__file__).parent / 'templates'
    required_templates = [
        'terms.html',
        'privacy.html',
        'integrated.html',
        'index.html',
        'video_result.html'
    ]

    all_exist = True

    for template in required_templates:
        template_path = templates_dir / template
        if template_path.exists():
            size = template_path.stat().st_size
            print(f"✅ {template:25} - Size: {size:,} bytes")
        else:
            print(f"❌ {template:25} - NOT FOUND")
            all_exist = False

    print("\n" + "="*60)
    if all_exist:
        print("🎉 All template files present!")
    else:
        print("⚠️  Some template files missing.")
    print("="*60)

    return all_exist

def check_footer_links():
    """Check that footer links are present in templates"""
    print("\n🔗 Checking Footer Links...\n")

    from pathlib import Path

    templates_dir = Path(__file__).parent / 'templates'
    templates_to_check = ['integrated.html', 'index.html', 'video_result.html']

    all_have_footer = True

    for template_name in templates_to_check:
        template_path = templates_dir / template_name
        if template_path.exists():
            content = template_path.read_text(encoding='utf-8')

            has_terms = '/terms' in content
            has_privacy = '/privacy' in content
            has_footer_class = 'footer' in content

            if has_terms and has_privacy and has_footer_class:
                print(f"✅ {template_name:25} - Footer with links present")
            else:
                print(f"❌ {template_name:25} - Footer incomplete")
                all_have_footer = False
        else:
            print(f"❌ {template_name:25} - File not found")
            all_have_footer = False

    print("\n" + "="*60)
    if all_have_footer:
        print("🎉 All templates have footer links!")
    else:
        print("⚠️  Some templates missing footer links.")
    print("="*60)

    return all_have_footer

if __name__ == '__main__':
    print("="*60)
    print("     TERMS & PRIVACY IMPLEMENTATION TEST")
    print("="*60)

    # Run all tests
    test1 = verify_templates()
    test2 = check_footer_links()
    test3 = test_routes()

    print("\n" + "="*60)
    print("           FINAL RESULT")
    print("="*60)

    if test1 and test2 and test3:
        print("\n✅ ✅ ✅  ALL TESTS PASSED!  ✅ ✅ ✅\n")
        print("Your Terms of Service and Privacy Policy pages are")
        print("fully implemented and ready for production!\n")
        print("🚀 You can now deploy to Railway.\n")
        sys.exit(0)
    else:
        print("\n⚠️  SOME TESTS FAILED\n")
        print("Please review the errors above and fix any issues.\n")
        sys.exit(1)
