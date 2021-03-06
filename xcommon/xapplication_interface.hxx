/*
* ****************************************************************************
* *                                                                          *
* * Copyright 2008, xWorkshop Inc.                                           *
* * All rights reserved.                                                     *
* * Redistribution and use in source and binary forms, with or without       *
* * modification, are permitted provided that the following conditions are   *
* * met:                                                                     *
* *    * Redistributions of source code must retain the above copyright     *
* * notice, this list of conditions and the following disclaimer.            *
* *    * Redistributions in binary form must reproduce the above             *
* * copyright notice, this list of conditions and the following disclaimer   *
* * in the documentation and/or other materials provided with the            *
* * distribution.                                                            *
* *    * Neither the name of xWorkshop Inc. nor the names of its             *
* * contributors may be used to endorse or promote products derived from     *
* * this software without specific prior written permission.                 *
* * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS     *
* * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT        *
* * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR    *
* * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT     *
* * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,    *
* * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT         *
* * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,    *
* * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY    *
* * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT      *
* * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE    *
* * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.     *
* *                                                                          *
* * Author: stoneyrh@163.com                                                 *
* *                                                                          *
* ****************************************************************************
*/

#ifndef _X_APPLICATION_INTERFACE_H_
#define _X_APPLICATION_INTERFACE_H_

#include "xglobal.hxx"
#include "xversion.hxx"
#include "xprogram_options.hxx"

namespace xws
{

class xapplication_interface
{
    public:
        xapplication_interface(int argc, xchar* argv[]);
        xapplication_interface(int argc, xchar* argv[], const xprogram_options::options_description& options_description);
        virtual ~xapplication_interface();

        virtual xstring name() const = 0;
        virtual int exec() { return 0; }
        virtual xstring version_str() const;
        virtual xstring legal_statement() const;
        virtual xstring bug_statement() const;
        //
        const xversion& version() const { return version_; }
        void set_version(xversion_t major_value, xversion_t minor_value, xversion_t release_value, xversion_t build_value)
        {
            version_.set(major_value, minor_value, release_value, build_value);
        }
        bool has_option(const astring& name) const;
        template <class T>
        T option_value(const astring& name, bool* defaulted = 0)
        {
            if (options_vars_.count(name))
            {
                if (defaulted)
                {
                    *defaulted = options_vars_[name].defaulted();
                }
                return options_vars_[name].as<T>();
            }
            // Use staic in case v won't have default constructor, like int
            static T value;
            return value;
        }
    private:
        xversion version_;
        xprogram_options::variables_map options_vars_;
};

} // namespace xws

#endif
