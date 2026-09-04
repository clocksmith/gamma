#include "tensor_container.hpp"

#include <exception>
#include <iostream>

namespace nncp = gamma_enwiki9::nncp;

int main(int argc, char** argv) {
  try {
    if (argc < 2) {
      std::cerr << "usage: " << argv[0] << " CONTAINER...\n";
      return 2;
    }
    for (int argument = 1; argument < argc; ++argument) {
      const nncp::TensorContainer container(argv[argument]);
      std::cout << "container\t" << container.path().string() << '\t'
                << container.configuration().size() << '\t'
                << container.tensors().size() << '\n';
      for (const nncp::TensorMetadata& tensor : container.tensors()) {
        std::cout << "tensor\t" << tensor.name << '\t' << tensor.type << '\t';
        for (std::size_t axis = 0; axis < tensor.dimensions.size(); ++axis) {
          if (axis != 0) std::cout << ',';
          std::cout << tensor.dimensions[axis];
        }
        std::cout << '\t' << tensor.elements << '\t' << tensor.bytes << '\n';
      }
    }
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "tensor manifest failed: " << error.what() << '\n';
    return 1;
  }
}
