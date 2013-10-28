/*
 * SchedulableInstruction.h
 *
 *  Created on: Oct 25, 2013
 *      Author: s7even
 */

#include <string>
#include <vector>

#ifndef SCHEDULABLEINSTRUCTION_H_
#define SCHEDULABLEINSTRUCTION_H_

class SchedulableInstruction {
//private:
//    std::string label;
//    std::string instruction;
//    vector<int> groups;
public:
    std::vector<std::string> label;
    std::vector<std::string> instruction;
    std::vector<int> groups;

    SchedulableInstruction();
    virtual ~SchedulableInstruction();
};

#endif /* SCHEDULABLEINSTRUCTION_H_ */
