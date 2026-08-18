#include <iostream>
#include <string>
#include "alife/version.h"

int main() {
    std::string version = alife::get_version();
    
    if (version.empty()) {
        std::cerr << "FAIL: version is empty" << std::endl;
        return 1;
    }
    
    std::cout << "PASS: version = " << version << std::endl;
    return 0;
}
