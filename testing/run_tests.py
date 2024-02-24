import test_apicall
import test_resource
import test_deployment


def run_tests():
    test_apicall.run_tests()
    test_resource.run_tests()
    test_deployment.run_tests()


if __name__ == "__main__":
    run_tests()