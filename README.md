# ATI_Jmeter
### 介绍
本项目介绍如何使用Jmeter+Ant+Python完成接口自动化测试。<br>

功能：<br>
1. 使用Jmeter维护接口测试用例；
2. 使用Ant执行测试任务，并生成测试报告；
3. 使用Python完成邮件发送及任务调度；
4. 通过get请求触发任务执行，调度方式灵活；
5. 具有定时功能，可周期性或者定时执行测试任务；
6. 通过监控端口，当服务重启后，可自动执行测试任务；

实现：<br>
1. 使用Ant执行Jmeter脚本，并生成测试报告；
2. 考虑到邮件正文内容可读性，定制化修改测试报告模板；
3. 使用正则表达式提取测试报告中的信息，重新组合成邮件正文；
4. 通过get请求触发测试任务的执行；
5. 通过线程池+队列的方式执行测试任务，可灵活设置线程池大小；
6. 使用aiohttp框架启动后台服务，将测试报告加入到静态资源中，可通过链接访问；

### 部署
1、Jmeter和Ant部署参考网上教程，主要介绍测试报告模板修改和build.xml文件<br>
    测试报告模板主要修改如下，其他小的修改这里不赘述，可使用文档比较工具自行比较查看，也可[在线文档比较](http://www.jq22.com/textDifference) ;<br>
    build.xml文件如下，具体配置已详细说明<br>

2、克隆repository<br>
    ```git clone https://github.com/leeyoshinari/ATI_Jmeter.git``` <br>

3、测试用例放置<br>
> (1)所有测试用例放在一个统一的文件夹中，例如`testCase`文件夹；<br>
> (2)针对不同系统的不同测试用例，可单独再放入一个文件夹中管理，例如：百度的测试用例放在`baidu`中、百度的BVT测试用例放在`baidu_bvt`中、腾讯的测试用例放在`tencent`中；<br>
> (3)每个测试用例文件夹中，都需要放一个配置好的`build.xml`文件；<br>

强烈建议文件夹及文件名称使用英文<br>
为什么要按照上面的要求放置测试用例？这样放置方便执行测试任务，通过get请求`http://ip:port/run/baidu`就可以执行百度的测试用例，请求`http://ip:port/run/baidu_bvt`就可以执行百度BVT的测试用例。<br>

4、修改配置文件<br>
> (1)线程池大小，建议设置1就够了；如确实调度较多测试用例的执行，可酌情增加；<br>
> (2)测试用例路径和测试报告路径，建议使用绝对路径；其中测试报告路径应和`build.xml`文件中的路径保持一致；<br>
> (3)邮件发送配置，请确认SMTP服务配置正确；邮箱登录密码配置，请在`sendEmail.py`文件中第48行设置，如果密码不想让其他人看到，请将该py文件进行编译，或者直接将这个repository打包，具体打包方法，请往下看；<br>

5、运行<br>
> Linux:<br>
> ```nohup python3 main.py &``` <br>
> Windows<br>
> ```python main.py``` <br>

6、打包<br>
经过前5步，如果该repository可以启动，且执行测试任务成功，则可以进行打包，使用pyinstaller进行打包。<br>
pyinstaller安装自行查找教程，须确保安装正确，否则打包会报错，下面直接进行打包：
> (1)进入ATI_Jmeter文件夹，执行命令：<br>
> ```shell
> pyinstaller main.py -p schedule.py -p logger.py -p config.py --hidden-import logger --hidden-import schedule --hidden-import config
> ```
> (2)打包完成后，在当前路径下会生成dist文件夹，进入dist/main即可找到可执行文件main;<br>
> (3)将配置文件config.conf拷贝到dist/main文件夹下，并修改配置文件；<br>
> (4)将dist/server整个文件夹拷贝到其他环境，启动main <br>
> ```nohup ./main &```

7、CI/CD，以Jenkins为例，在Jenkins构建后操作中增加一个get请求，请求的url为`http://IP:PORT/run/系统名称`，此处系统名称应和testCase用例文件夹中的对应的系统名称保持一致。

8、如果你所在的项目还没有用到CI/CD，或者项目本身有较多配置项，每次手动更改配置重启后，也想自动执行测试任务；亦或是你不想配置CI/CD，则需要执行客户端；<br>
进入client文件夹，将脚本和配置文件拷贝到项目所在的服务器上，运行即可，也可以按照步骤6的方式进行打包。<br>

修改配置文件：<br>
> (1)系统名称必须和测试用例文件夹中的名称保持一致，例如可配置成`baidu`；如需测试多个系统，名字用英文逗号`,`隔开；<br>
> (2)端口号即系统占用的端口号；如需监控多个系统的端口，端口用英文逗号`,`隔开；<br>
注意：如测试多个系统，系统的排序和端口的排序必须保持一致

### 注意
1、如需部署client，部署的服务器必须支持`netstat`命令，以便根据端口号查进程号；仅支持Linux系统；<br>
2、已经测试的版本：Jmeter-5.2.1、Ant-1.10.7

### Requirements
1. aiohttp>=3.6.2
2. requests
3. Python 3.7+
